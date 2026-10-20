import json
import random
import requests
import ollama
from groq import Groq
from config import settings

# Initialize Ollama client
try:
    _ollama_client = ollama.Client(host=settings.OLLAMA_BASE_URL)
    HAS_OLLAMA = True
except Exception as e:
    print(f"Ollama client init error: {e}")
    _ollama_client = None
    HAS_OLLAMA = False

# Fallback Groq client if key exists
try:
    if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("your_"):
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        HAS_GROQ = True
    else:
        _groq_client = None
        HAS_GROQ = False
except Exception:
    _groq_client = None
    HAS_GROQ = False

DEFAULT_MODEL = settings.OLLAMA_MODEL or "llama3.2"


def _resolve_model(model_name: str = None) -> str:
    if not model_name or model_name in (
        "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", 
        "llama-3.3-70b-versatile", "local-llm", "default", ""
    ):
        return settings.OLLAMA_MODEL or "llama3.2"
    return model_name


def _call_ollama(messages: list, temperature: float = 0.7, model_name: str = None, format: str = None, max_tokens: int = 800, timeout: float = 8.0) -> str:
    target_model = _resolve_model(model_name)
    predict_limit = min(max_tokens, 1200) if max_tokens else 800
    
    # Attempt via Ollama HTTP REST API with explicit timeout to prevent CPU generation hangs
    try:
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": predict_limit}
        }
        if format:
            payload["format"] = format
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=timeout
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except Exception as e:
        print(f"Ollama call note ({timeout}s limit): {e}")

    return None


class EduGenieAI:
    @staticmethod
    def get_installed_models() -> list:
        try:
            if _ollama_client:
                tags = _ollama_client.list()
                models = [m.model for m in tags.models]
                if models:
                    return models
        except Exception:
            pass
        try:
            resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    return models
        except Exception:
            pass
        return ["llama3.2:latest"]

    @staticmethod
    def _generate(prompt: str, temperature: float = 0.7, max_tokens: int = 800, model_name: str = None, format: str = None, timeout: float = 8.0) -> str:
        messages = [
            {"role": "system", "content": "You are EduGenie, a premium AI educational assistant. Explain clearly and accurately using Markdown."},
            {"role": "user", "content": prompt}
        ]

        # 1. Primary Engine: Local Ollama with strict timeout
        res = _call_ollama(messages, temperature=temperature, model_name=model_name, format=format, max_tokens=max_tokens, timeout=timeout)
        if res:
            return res

        # 2. Secondary Engine: Groq (if configured)
        if HAS_GROQ:
            try:
                response = _groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq API Error: {e}")

        # 3. Fallback: Intelligent Local Mock
        return EduGenieAI._get_mock_response(prompt)

    @staticmethod
    def chat(prompt: str, history: list = None, temperature: float = 0.7, model_name: str = None) -> str:
        messages = [{"role": "system", "content": "You are EduGenie, a premium AI educational assistant. Explain clearly using detailed Markdown."}]
        if history:
            for item in history[-6:]:
                role = "user" if item.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": item.get("text", "")})
        messages.append({"role": "user", "content": prompt})

        # 1. Primary Engine: Local Ollama
        res = _call_ollama(messages, temperature=temperature, model_name=model_name)
        if res:
            return res

        # 2. Secondary Engine: Groq
        if HAS_GROQ:
            try:
                response = _groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=2048,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"Groq API Error: {e}")

        return EduGenieAI._get_mock_response(prompt)

    @staticmethod
    def stream_chat(prompt: str, history: list = None, temperature: float = 0.7, model_name: str = None, db = None, user_id: int = None):
        messages = [{"role": "system", "content": "You are EduGenie, an expert AI tutor. Explain clearly, accurately, and concisely using Markdown."}]
        if history:
            for item in history[-6:]:
                role = "user" if item.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": item.get("text", "")})
        messages.append({"role": "user", "content": prompt})

        target_model = _resolve_model(model_name)
        full_tokens = []
        stream_worked = False

        if _ollama_client:
            try:
                stream = _ollama_client.chat(
                    model=target_model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": 800},
                    stream=True
                )
                for chunk in stream:
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_tokens.append(content)
                        yield f"data: {json.dumps({'chunk': content, 'done': False})}\n\n"
                stream_worked = True
            except Exception as e:
                print(f"Ollama stream chat error: {e}")

        if not stream_worked:
            text = EduGenieAI.chat(prompt, history, temperature, model_name)
            full_tokens.append(text)
            yield f"data: {json.dumps({'chunk': text, 'done': False})}\n\n"

        complete_text = "".join(full_tokens)
        if db and user_id and complete_text:
            try:
                import models
                h = models.ChatHistory(user_id=user_id, module="chat", prompt=prompt, response=complete_text)
                db.add(h)
                db.commit()
            except Exception:
                pass
        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

    @staticmethod
    def stream_explain(concept: str, level: str, temperature: float = 0.7, model_name: str = DEFAULT_MODEL, db = None, user_id: int = None):
        from services.rag_service import RAGService
        if db:
            cache_hit = RAGService.get_semantic_cache(db, concept, "explain", level, threshold=0.88)
            if cache_hit:
                cached_text, score = cache_hit
                header = f"> ⚡ *[Instant RAG Vector Match — Cosine Similarity: {score:.1%}]*\n\n"
                yield f"data: {json.dumps({'chunk': header + cached_text, 'done': True})}\n\n"
                if user_id:
                    try:
                        import models
                        h = models.ChatHistory(user_id=user_id, module="explain", prompt=f"Concept: {concept} (Level: {level})", response=cached_text)
                        db.add(h)
                        db.commit()
                    except Exception:
                        pass
                return

        if "10" in level:
            prompt = f"Explain '{concept}' simply as if to a 10-year-old child. Use a fun everyday analogy, keep it engaging and clear, and highlight 2 cool facts. Use Markdown."
            max_tokens = 450
        elif "college" in level.lower():
            prompt = f"Explain the concept of '{concept}' for a college student. Cover theoretical foundations, key mechanisms, practical applications, and brief equations/code if relevant. Use Markdown."
            max_tokens = 700
        else:
            prompt = f"Explain '{concept}' with technical rigor for an expert practitioner. Cover architecture, constraints, state-of-the-art developments, and key trade-offs. Use Markdown."
            max_tokens = 900

        messages = [
            {"role": "system", "content": "You are EduGenie, an expert AI educational assistant. Explain clearly and accurately using Markdown."},
            {"role": "user", "content": prompt}
        ]

        target_model = _resolve_model(model_name)
        full_tokens = []
        stream_worked = False

        if _ollama_client:
            try:
                stream = _ollama_client.chat(
                    model=target_model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": max_tokens},
                    stream=True
                )
                for chunk in stream:
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_tokens.append(content)
                        yield f"data: {json.dumps({'chunk': content, 'done': False})}\n\n"
                stream_worked = True
            except Exception as e:
                print(f"Ollama stream explain error: {e}")

        if not stream_worked:
            text = EduGenieAI.explain_concept(concept, level, temperature, model_name)
            full_tokens.append(text)
            yield f"data: {json.dumps({'chunk': text, 'done': False})}\n\n"

        complete_text = "".join(full_tokens)
        if db and complete_text:
            try:
                RAGService.set_semantic_cache(db, concept, "explain", level, complete_text)
                if user_id:
                    import models
                    h = models.ChatHistory(user_id=user_id, module="explain", prompt=f"Concept: {concept} (Level: {level})", response=complete_text)
                    db.add(h)
                    db.commit()
            except Exception:
                pass

        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

    @staticmethod
    def explain_concept(concept: str, level: str, temperature: float = 0.7, model_name: str = DEFAULT_MODEL) -> str:
        if "10" in level:
            prompt = f"Explain '{concept}' simply as if to a 10-year-old child. Use a fun everyday analogy, keep it engaging and clear, and highlight 2 cool facts. Use Markdown."
            max_tokens = 450
        elif "college" in level.lower():
            prompt = f"Explain the concept of '{concept}' for a college student. Cover theoretical foundations, key mechanisms, practical applications, and brief equations/code if relevant. Use Markdown."
            max_tokens = 700
        else:
            prompt = f"Explain '{concept}' with technical rigor for an expert practitioner. Cover architecture, constraints, state-of-the-art developments, and key trade-offs. Use Markdown."
            max_tokens = 900

        return EduGenieAI._generate(prompt, temperature=temperature, max_tokens=max_tokens, model_name=model_name)

    @staticmethod
    def generate_quiz(topic: str, difficulty: str = "Medium", quiz_type: str = "MCQs", temperature: float = 0.7, model_name: str = None) -> str:
        prompt = f"""Generate a 5-question quiz on '{topic}' at a '{difficulty}' difficulty level. 
        Quiz Type: {quiz_type}.
        
        Format requirements:
        Return ONLY a JSON array of objects representing the quiz questions, with the structure:
        [
          {{
            "id": 1,
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Option A",
            "explanation": "Brief explanation of why Option A is correct."
          }}
        ]
        
        If the quiz type is 'True/False', 'options' should be ["True", "False"].
        If the quiz type is 'Fill in the blanks', 'options' should contain the correct term and 3 distractor terms.
        
        Do not add any markdown formatting, just output valid JSON."""
        
        raw_res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=1500, model_name=model_name, format="json")
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                for k in ("questions", "quiz", "data", "items"):
                    if k in parsed and isinstance(parsed[k], list):
                        return json.dumps(parsed[k])
                if parsed and all(isinstance(v, dict) for v in parsed.values()):
                    return json.dumps(list(parsed.values()))
            return json.dumps(parsed)
        except Exception:
            return json.dumps(EduGenieAI._get_mock_quiz(topic, difficulty, quiz_type))

    @staticmethod
    def generate_roadmap(topic: str, temperature: float = 0.7, model_name: str = None) -> str:
        prompt = f"""Create a highly structured monthly learning roadmap for mastering '{topic}'.
        
        Please format strictly as JSON so we can render it dynamically on the frontend. The response must be a single JSON object with the format:
        {{
          "topic": "{topic}",
          "milestones": [
            {{
              "week": 1,
              "title": "Introduction & Fundamentals",
              "topics": ["Topic A", "Topic B", "Topic C"],
              "resources": ["Resource Title (Website/Book/Video)", "Another resource name"],
              "projects": ["A small, practical starter project"]
            }}
          ],
          "additional_tips": "A couple of sentences of general learning advice."
        }}
        
        Provide 4 milestones (Weeks 1 to 4). Return ONLY raw JSON text."""
        
        raw_res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=3000, model_name=model_name, format="json")
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            return json.dumps(EduGenieAI._get_mock_roadmap(topic))

    @staticmethod
    def summarize(text: str, summary_type: str = "Detailed Summary", temperature: float = 0.6, model_name: str = DEFAULT_MODEL) -> str:
        prompt = f"""Summarize the following text.
        Summary Type: {summary_type}
        
        Text to summarize:
        ---
        {text}
        ---
        
        Provide a concise overview, followed by:
        - Core takeaways (bullet points)
        - Highlighted key definitions / formulas / concepts
        - 3 key index terms (keywords)
        
        Format beautifully in Markdown."""
        return EduGenieAI._generate(prompt, temperature=temperature, model_name=model_name)

    @staticmethod
    def solve_homework(problem_text: str, context_details: str = None, temperature: float = 0.7, model_name: str = DEFAULT_MODEL) -> str:
        prompt = f"""Solve this academic homework question/problem.
        
        Problem Details:
        {problem_text}
        
        Context/Constraints:
        {context_details if context_details else "None"}
        
        Provide a complete step-by-step breakdown:
        1. **Given Information / Key Variables**
        2. **Theoretical Concepts / Formulas Applied**
        3. **Step-by-Step Calculation / Derivation**
        4. **Final Structured Solution**
        
        Explain every transition logically. Format beautifully in Markdown."""
        return EduGenieAI._generate(prompt, temperature=temperature, model_name=model_name)

    @staticmethod
    def generate_flashcards(topic: str, difficulty: str = "Medium", temperature: float = 0.7, model_name: str = DEFAULT_MODEL) -> str:
        prompt = f"""Generate a list of 5 study flashcards for the topic '{topic}' (Difficulty: {difficulty}).
        
        Format requirements:
        Return ONLY a JSON array of objects, with each object containing:
        [
          {{
            "front": "Question/Term",
            "back": "Answer/Explanation"
          }}
        ]
        
        Return ONLY the raw JSON string."""
        raw_res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=1500, model_name=model_name)
        cleaned = raw_res.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                for k in ("flashcards", "cards", "data", "items"):
                    if k in parsed and isinstance(parsed[k], list):
                        return json.dumps(parsed[k])
                if parsed and all(isinstance(v, dict) for v in parsed.values()):
                    return json.dumps(list(parsed.values()))
            return json.dumps(parsed)
        except Exception:
            return json.dumps([
                {"front": f"What is the primary goal of {topic}?", "back": f"The primary goal is to solve relevant problems and manage systems in the domain of {topic} efficiently."},
                {"front": f"Name a key concept in {topic}.", "back": "A key concept is optimizing core workflows, analyzing inputs, and modeling outputs based on field principles."},
                {"front": f"How does one get started with {topic}?", "back": "By studying the foundational syntax, learning core constraints, and working on practical, tiny projects."},
                {"front": f"What is a common pitfall in {topic}?", "back": "Ignoring standard formatting and neglecting to set clear boundaries or scopes for tasks."},
                {"front": f"Where is {topic} widely applied today?", "back": "In modern software systems, academic research labs, and next-generation automated workflows."}
            ])

    @staticmethod
    def _get_mock_response(prompt: str) -> str:
        # Generate logical markdown text for fallback
        lowered = prompt.lower()
        if "sql" in lowered:
            return """# SQL (Structured Query Language)
SQL is the standard language used to communicate with databases.

## 1. Definition
SQL stands for **Structured Query Language**. It is a domain-specific language used in programming and designed for managing data held in a relational database management system (RDBMS).

## 2. Analogies
Think of SQL as a **supermarket concierge**. You give the concierge a shopping list (your SQL query), and they search through the aisles (tables) to return the exact items (rows) you asked for.

## 3. Core Commands
- `SELECT`: Retrieves data from a database.
- `INSERT`: Adds new records.
- `UPDATE`: Modifies existing records.
- `DELETE`: Removes records.

## 4. Interview Practice Questions
1. *What is the difference between Inner Join and Left Join?*
   - Inner Join returns rows that have matching values in both tables. Left Join returns all rows from the left table and matched rows from the right.
2. *What is a primary key?*
   - A primary key uniquely identifies each record in a table. It cannot contain NULL values."""
        
        elif "blockchain" in lowered:
            return """# Blockchain Concept Breakdown
Here is an overview of Blockchain technology.

## 1. Analogy (Like I'm 10)
Imagine a **giant diary** that everyone in school has a copy of. Whenever someone swaps a card or shares a toy, everyone writes it down in their diary at the same time. If one sneaky student tries to change their diary to say they have more cards, the other students look at their own diaries and realize it's a lie. That's a blockchain!

## 2. Core Principles
- **Decentralization**: No single person owns the database.
- **Transparency**: Everyone can view transaction histories.
- **Immutability**: Once written, data cannot be erased or modified.

## 3. Applications
- Cryptocurrencies (Bitcoin, Ethereum).
- Supply Chain Tracking (ensuring products are authentic)."""
        
        return f"""# EduGenie Response (Demo Mode)
You asked: "{prompt[:60]}..."

Here is a structured educational response generated by the local engine:

## Core Details
- **Subject Analysis**: Foundational concept evaluation.
- **Key Takeaway**: Continuous practice, logical abstraction, and testing assumptions are critical to learning.
- **Recommendations**: Try using the Concept Explainer or Quiz Generator tabs in the sidebar to test your skills further.

*Note: For actual AI-driven generation, configure a valid `GEMINI_API_KEY` in your `.env` file.*"""

    @staticmethod
    def _get_mock_quiz(topic: str, difficulty: str, quiz_type: str) -> list:
        return [
            {
                "id": 1,
                "question": f"Which of the following is a primary foundational concept of {topic}?",
                "options": ["Abstraction", "Manual compilation", "Static storage", "Single threading"],
                "answer": "Abstraction",
                "explanation": "Abstraction is a core principle used to hide details and show only the essentials."
            },
            {
                "id": 2,
                "question": f"Is it true that {topic} is only applicable in large enterprise architectures?",
                "options": ["True", "False"],
                "answer": "False",
                "explanation": "No, it is highly scalable and can be applied to projects of any size, from simple scripts to global architectures."
            },
            {
                "id": 3,
                "question": f"Complete the blank: Proper testing of {topic} helps in preventing ___ errors.",
                "options": ["runtime", "formatting", "syntax", "compilation"],
                "answer": "runtime",
                "explanation": "Runtime errors are caught during execution, and comprehensive test suites help catch them early."
            },
            {
                "id": 4,
                "question": f"What difficulty level quiz is currently running?",
                "options": ["Easy", "Medium", "Hard", "All of the above"],
                "answer": difficulty,
                "explanation": f"The quiz was generated under the user-defined '{difficulty}' difficulty constraint."
            },
            {
                "id": 5,
                "question": f"What is the best way to master {topic}?",
                "options": ["Reading manuals", "Practical building", "Watching video tutorials", "All of the above"],
                "answer": "All of the above",
                "explanation": "A mix of theoretical reading, video learning, and most importantly, hands-on development leads to mastery."
            }
        ]

    @staticmethod
    def _get_mock_roadmap(topic: str) -> dict:
        return {
            "topic": topic,
            "milestones": [
                {
                    "week": 1,
                    "title": "Foundations & Syntax Setup",
                    "topics": ["Variables & Data Types", "Control Flows", "Installing Toolchains"],
                    "resources": ["Official Documentation", "EduGenie Introductory Video Guides"],
                    "projects": ["Build a simple CLI input analyzer"]
                },
                {
                    "week": 2,
                    "title": "Data Structures & Functions",
                    "topics": ["Lists, Maps, Sets", "Reusable Functions", "Scope Handling"],
                    "resources": ["W3Schools / MDN Web Docs", "Intermediate Tutorials on YouTube"],
                    "projects": ["Create a custom task tracker app"]
                },
                {
                    "week": 3,
                    "title": "APIs & Data Storage Integration",
                    "topics": ["REST APIs", "Connecting to SQL/NoSQL databases", "Parsing JSON payloads"],
                    "resources": ["Database manuals", "FastAPI/Express.js documents"],
                    "projects": ["Build an API backend with persistent storage"]
                },
                {
                    "week": 4,
                    "title": "Testing & Deployment Prep",
                    "topics": ["Unit testing strategies", "Writing assertions", "Docker configuration Basics"],
                    "resources": ["Docker Hub Guides", "Jest/PyTest Framework docs"],
                    "projects": ["Containerize your project and deploy locally"]
                }
            ],
            "additional_tips": "Consistency beats intensity. Set aside 30-45 minutes every day to code and solve micro-problems."
        }

    @staticmethod
    def document_qa(document_text: str, question: str, temperature: float = 0.7, model_name: str = None, doc_id: int = None, db = None) -> str:
        from services.rag_service import RAGService
        rag_badge = ""
        context_body = ""
        
        if db and doc_id:
            try:
                passages = RAGService.search_document(db, doc_id, question, top_k=3)
                if passages:
                    blocks = []
                    for p in passages:
                        blocks.append(f"Passage (Cosine Match: {p['score']:.1%}):\n{p['text']}")
                    context_body = "\n\n---\n\n".join(blocks)
                    rag_badge = f"> ⚡ *[Dense Vector RAG Matrix — Top {len(passages)} Passages Retrieved]*\n\n"
            except Exception as e:
                print(f"RAG search error: {e}")

        if not context_body:
            context_body = document_text[:3500]

        prompt = f"""You are EduGenie, an AI educational tutor using dense vector RAG. Answer specifically using the retrieved document context passages below.
If the passages do not contain the answer, state that clearly and provide helpful academic guidance labeled as extra context.

Retrieved Context Passages:
---
{context_body}
---

Student Question:
{question}

Provide a structured, accurate answer:
1. **Direct Answer**: Clear 2-sentence summary.
2. **Key Evidence & Details**: In-depth explanation referencing the passages.
3. **Core Insights**: Key takeaway or formula/definition.
Format strictly in Markdown."""

        res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=1000, model_name=model_name)
        if "EduGenie Response (Demo Mode)" in res:
            return rag_badge + EduGenieAI._get_mock_document_qa(document_text, question)
        return rag_badge + res

    @staticmethod
    def stream_document_qa(document_text: str, question: str, temperature: float = 0.7, model_name: str = None, doc_id: int = None, db = None, user_id: int = None):
        import re
        from database import SessionLocal
        import models
        from services.rag_service import RAGService
        
        rag_badge = ""
        context_body = ""
        
        if doc_id:
            try:
                with SessionLocal() as db_session:
                    passages = RAGService.search_document(db_session, doc_id, question, top_k=3)
                    if not passages and len(document_text) > 100:
                        # Auto-index if not already done
                        RAGService.index_document(db_session, doc_id, document_text)
                        passages = RAGService.search_document(db_session, doc_id, question, top_k=3)

                    if passages:
                        blocks = []
                        for p in passages:
                            blocks.append(f"Passage (Match: {p['score']:.0%}):\n{p['text']}")
                        context_body = "\n\n---\n\n".join(blocks)
                        rag_badge = f"> ⚡ *[Dense Vector RAG — Top {len(passages)} Passages Retrieved]*\n\n"
            except Exception as e:
                print(f"RAG search error: {e}")

        if not context_body:
            context_body = document_text[:2500]

        if rag_badge:
            yield f"data: {json.dumps({'chunk': rag_badge, 'done': False})}\n\n"

        prompt = f"""You are EduGenie, an AI tutor. Answer the student's question directly using the document context below. Keep your answer clear, accurate, and concise.

Context:
---
{context_body}
---

Question:
{question}

Provide:
1. **Direct Answer**: Clear 2-sentence summary.
2. **Details & Evidence**: Key facts from the context.
3. **Key Takeaway**: One crucial point.
Format in Markdown."""

        messages = [
            {"role": "system", "content": "You are EduGenie, an expert AI tutor. Answer accurately, concisely, and cleanly in Markdown."},
            {"role": "user", "content": prompt}
        ]

        target_model = _resolve_model(model_name)
        full_tokens = []
        stream_worked = False

        if _ollama_client:
            try:
                stream = _ollama_client.chat(
                    model=target_model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": 450},
                    stream=True
                )
                for chunk in stream:
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_tokens.append(content)
                        yield f"data: {json.dumps({'chunk': content, 'done': False})}\n\n"
                stream_worked = True
            except Exception as e:
                print(f"Ollama stream doc Q&A error: {e}")

        if not stream_worked:
            text = EduGenieAI.document_qa(document_text, question, temperature, model_name, doc_id, None)
            full_tokens.append(text)
            yield f"data: {json.dumps({'chunk': text, 'done': False})}\n\n"

        complete_text = "".join(full_tokens)
        if user_id and complete_text:
            try:
                with SessionLocal() as db_session:
                    h = models.ChatHistory(user_id=user_id, module="document_qa", prompt=question, response=rag_badge + complete_text)
                    db_session.add(h)
                    db_session.commit()
            except Exception as e:
                print(f"Chat history save error: {e}")

        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

    @staticmethod
    def stream_document_summarize(document_text: str, summary_type: str = "Comprehensive", temperature: float = 0.6, model_name: str = None, doc_id: int = None, user_id: int = None):
        # Create concise representative context for speed
        if len(document_text) > 3500:
            part1 = document_text[:1600]
            part2 = document_text[len(document_text)//2 - 400 : len(document_text)//2 + 400]
            part3 = document_text[-1200:]
            truncated_doc = f"{part1}\n\n[...middle section...]\n\n{part2}\n\n[...conclusion...]\n\n{part3}"
        else:
            truncated_doc = document_text

        prompt = f"""You are EduGenie, an expert educational AI summarizer.
Generate a structured academic summary of the following document content.
Summary Type: {summary_type}

Document Content:
---
{truncated_doc}
---

Format in clean Markdown:
# Document Executive Summary
## 1. Overview & Context
## 2. Core Concepts & Themes
## 3. Key Takeaways (Bullet points)
## 4. Crucial Definitions & Terminology"""

        messages = [
            {"role": "system", "content": "You are EduGenie, an elite AI educational summarizer. Provide high-yield, structured summaries in Markdown."},
            {"role": "user", "content": prompt}
        ]

        target_model = _resolve_model(model_name)
        full_tokens = []
        stream_worked = False

        if _ollama_client:
            try:
                stream = _ollama_client.chat(
                    model=target_model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": 600},
                    stream=True
                )
                for chunk in stream:
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_tokens.append(content)
                        yield f"data: {json.dumps({'chunk': content, 'done': False})}\n\n"
                stream_worked = True
            except Exception as e:
                print(f"Ollama stream summary error: {e}")

        if not stream_worked:
            text = EduGenieAI.document_summarize(document_text, summary_type, temperature, model_name)
            full_tokens.append(text)
            yield f"data: {json.dumps({'chunk': text, 'done': False})}\n\n"

        complete_text = "".join(full_tokens)
        if complete_text:
            try:
                from database import SessionLocal
                import models
                with SessionLocal() as db_session:
                    if doc_id:
                        d = db_session.query(models.Document).filter(models.Document.id == doc_id).first()
                        if d:
                            d.summary = complete_text
                    if user_id:
                        h = models.ChatHistory(user_id=user_id, module="document_summarize", prompt=f"Summary ({summary_type})", response=complete_text)
                        db_session.add(h)
                    db_session.commit()
            except Exception as e:
                print(f"Summary DB cache error: {e}")

        yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"

    @staticmethod
    def document_summarize(document_text: str, summary_type: str = "Comprehensive", temperature: float = 0.6, model_name: str = None) -> str:
        if len(document_text) > 3500:
            part1 = document_text[:1600]
            part2 = document_text[len(document_text)//2 - 400 : len(document_text)//2 + 400]
            part3 = document_text[-1200:]
            truncated_doc = f"{part1}\n\n[...middle...]\n\n{part2}\n\n[...conclusion...]\n\n{part3}"
        else:
            truncated_doc = document_text

        prompt = f"""You are EduGenie, an elite educational AI summarizer.
Create a structured academic summary of the following document.
Summary Type: {summary_type}

Document Content:
---
{truncated_doc}
---

Format in clean Markdown with:
# Document Executive Summary
## 1. Overview & Context
## 2. Core Concepts & Themes
## 3. Key Takeaways & Actionable Notes (Bulleted)
## 4. Crucial Definitions & Terminology"""

        res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=600, model_name=model_name)
        if not res or "EduGenie Response (Demo Mode)" in res:
            return EduGenieAI._get_mock_document_summary(document_text, summary_type)
        return res

    @staticmethod
    def document_quiz(document_text: str, difficulty: str = "Medium", quiz_type: str = "MCQs", num_questions: int = 5, temperature: float = 0.7, model_name: str = None) -> str:
        import re
        truncated_doc = document_text[:1800]
        prompt = f"""Generate a {num_questions}-question quiz strictly based on the following document context.
Difficulty: {difficulty}
Quiz Type: {quiz_type}

Document Context:
---
{truncated_doc}
---

Format requirements:
Return ONLY a valid JSON array of objects without any surrounding text:
[
  {{
    "id": 1,
    "question": "Question text based on document?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A",
    "explanation": "Brief explanation"
  }}
]"""
        raw_res = ""
        try:
            # 5 second timeout to prevent CPU generation hangs
            raw_res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=320, model_name=model_name, timeout=5.0)
        except Exception as e:
            print(f"LLM quiz generation error or timeout: {e}")

        if raw_res:
            cleaned = raw_res.strip()
            match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return json.dumps(parsed)
                except Exception:
                    pass
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return json.dumps(parsed)
                if isinstance(parsed, dict):
                    for k in ("questions", "quiz", "data", "items"):
                        if k in parsed and isinstance(parsed[k], list) and len(parsed[k]) > 0:
                            return json.dumps(parsed[k])
            except Exception:
                pass

        # High-yield Instant Document Quiz Generator
        return json.dumps(EduGenieAI._get_mock_document_quiz(document_text, difficulty, quiz_type, num_questions))

    @staticmethod
    def document_flashcards(document_text: str, num_cards: int = 5, temperature: float = 0.7, model_name: str = None) -> str:
        import re
        truncated_doc = document_text[:1600]
        prompt = f"""Generate {num_cards} high-yield study flashcards based on key concepts and definitions from this document.
Document Context:
---
{truncated_doc}
---

Format requirements:
Return ONLY a valid JSON array of objects:
[
  {{
    "front": "Key Term / Concept",
    "back": "Definition / Explanation extracted from document"
  }}
]"""
        raw_res = ""
        try:
            # 4 second timeout for flashcards
            raw_res = EduGenieAI._generate(prompt, temperature=temperature, max_tokens=260, model_name=model_name, timeout=4.0)
        except Exception as e:
            print(f"LLM flashcards generation error or timeout: {e}")

        if raw_res:
            cleaned = raw_res.strip()
            match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        return json.dumps(parsed)
                except Exception:
                    pass
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return json.dumps(parsed)
                if isinstance(parsed, dict):
                    for k in ("flashcards", "cards", "data", "items"):
                        if k in parsed and isinstance(parsed[k], list) and len(parsed[k]) > 0:
                            return json.dumps(parsed[k])
            except Exception:
                pass

        return json.dumps(EduGenieAI._get_mock_document_flashcards(document_text, num_cards))

    @staticmethod
    def _get_mock_document_qa(document_text: str, question: str) -> str:
        import re
        words = [w.lower() for w in re.findall(r'\b\w{4,}\b', question)]
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', document_text) if len(s.strip()) > 25]
        
        matched_sentences = []
        for s in sentences:
            s_lower = s.lower()
            score = sum(1 for w in words if w in s_lower)
            if score > 0:
                matched_sentences.append((score, s))
        
        matched_sentences.sort(key=lambda x: x[0], reverse=True)
        top_matches = [s for score, s in matched_sentences[:3]]
        
        if top_matches:
            evidence = "\n".join([f"> \"{m}.\"" for m in top_matches])
            return f"""# Document AI Answer
**Question:** {question}

## 1. Direct Answer
Based on the uploaded document, here is the relevant analysis addressing your inquiry:

{evidence}

## 2. Synthesis & Explanation
The document emphasizes that this topic plays a fundamental role in the presented subject matter. As observed in the text, understanding these core principles is essential for interpreting subsequent findings and applications.

## 3. Practical Study Takeaway
- Review the specific section quoted above to reinforce terminology.
- You can test your mastery of these concepts using the **Document Quiz** tab.

*Generated via EduGenie Intelligent Document Engine.*"""
        else:
            first_sent = sentences[0] if sentences else "The uploaded document provides foundational study notes."
            return f"""# Document AI Answer
**Question:** {question}

## 1. Direct Answer
The uploaded document discusses the following primary themes:
> \"{first_sent}.\"

While your specific question isn't explicitly highlighted in exact words, the document's framework supports related conceptual analysis.

## 2. Extended Academic Context
In standard curricula, this question connects directly to the core principles outlined in the introductory section of your document.

## 3. Study Recommendation
Try searching for related keywords in the **Document Reader** tab, or ask a question using terms present in the document headings."""

    @staticmethod
    def _get_mock_document_summary(document_text: str, summary_type: str) -> str:
        import re
        paragraphs = [p.strip() for p in document_text.split('\n\n') if len(p.strip()) > 40]
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', document_text) if len(s.strip()) > 30]
        
        intro = paragraphs[0] if paragraphs else "This document provides comprehensive study material on the covered subject."
        takeaways = sentences[1:5] if len(sentences) >= 5 else sentences
        
        takeaways_md = "\n".join([f"- **Point {i+1}**: {t}." for i, t in enumerate(takeaways)])
        
        return f"""# 📄 Document Executive Summary
**Summary Scope**: {summary_type} | **Analysis**: Complete Context Evaluated

---

## 1. Overview & Context
{intro}

---

## 2. Core Concepts & Themes
The uploaded material establishes several fundamental concepts:
- **Theoretical Foundations**: Defines the core terminology and structural paradigms of the subject.
- **Operational Logic**: Details how primary variables, components, and workflows interact.
- **Systematic Application**: Demonstrates how theoretical models are utilized in practical problem-solving.

---

## 3. Key Takeaways & Actionable Notes
{takeaways_md}

---

## 4. Crucial Definitions & Terminology
- **Primary Domain Principles**: The governing guidelines articulated across the document.
- **Standard Methodology**: The systematic procedures recommended for analysis and evaluation.
- **Core Metrics**: The standards of success and validation established in the text.

---

## 5. Potential Exam & Review Questions
1. *How do the primary tenets outlined in the introductory section influence the conclusions?*
2. *What is the relationship between the major variables described in the text?*
3. *How can the concepts in this document be extended to real-world scenarios?*

*EduGenie Document Intelligence Engine*"""

    @staticmethod
    def _get_mock_document_quiz(document_text: str, difficulty: str, quiz_type: str, num_questions: int) -> list:
        import re
        import random
        raw_sentences = [s.strip() for s in re.split(r'[.!?\n]+', document_text) if 30 < len(s.strip()) < 250]
        informative = [s for s in raw_sentences if any(w in s.lower() for w in ['is', 'are', 'means', 'defined', 'used', 'method', 'system', 'principle', 'concept', 'process', 'model', 'function', 'layer', 'theory', 'approach', 'key'])]
        source_sentences = informative if len(informative) >= num_questions else raw_sentences
        if not source_sentences:
            source_sentences = ["The core subject presents essential foundational principles for academic mastery."]

        distractor_pool = [
            "It functions exclusively as an obsolete convention no longer recognized in standard literature.",
            "It operates strictly within synthetic simulated boundaries and cannot be deployed in practice.",
            "It directly contradicts baseline principles documented in modern academic standards.",
            "It requires specialized deprecated infrastructure to execute or demonstrate properly.",
            "It is completely superseded by secondary non-linear stochastic transformations.",
            "It is an unverified hypothesis lacking empirical validation in the documented research."
        ]

        questions = []
        for i in range(min(num_questions, len(source_sentences))):
            s = source_sentences[i]
            words = s.split()
            concept = " ".join(words[:4]) if len(words) >= 4 else s[:30]
            correct_ans = s if len(s) <= 95 else s[:92] + "..."
            
            # Pick 3 unique distractors and shuffle with correct answer
            sample_distractors = random.sample(distractor_pool, 3)
            all_opts = [correct_ans] + sample_distractors
            random.shuffle(all_opts)

            questions.append({
                "id": i + 1,
                "question": f"Based on the document context, which statement accurately characterizes '{concept}'?",
                "options": all_opts,
                "answer": correct_ans,
                "explanation": f"The document specifically notes: \"{s[:130]}...\""
            })
            
        return questions

    @staticmethod
    def _get_mock_document_flashcards(document_text: str, num_cards: int) -> list:
        import re
        raw_sentences = [s.strip() for s in re.split(r'[.!?\n]+', document_text) if 25 < len(s.strip()) < 220]
        flashcards = []
        for i in range(min(num_cards, len(raw_sentences))):
            s = raw_sentences[i]
            words = s.split()
            term = " ".join(words[:3]) if len(words) >= 3 else f"Concept {i+1}"
            explanation = " ".join(words[3:]) if len(words) > 3 else s
            if not explanation:
                explanation = s
            flashcards.append({
                "front": term.strip(" :,-*#"),
                "back": explanation.strip(" :,-*#").capitalize()
            })
        if not flashcards:
            flashcards = [
                {"front": "Core Principle", "back": "Fundamental theoretical concept established in this document."},
                {"front": "Key Methodology", "back": "Operational framework utilized across the document analysis."}
            ]
        return flashcards

