import json
import math
import re
from typing import List, Dict, Optional, Tuple
import numpy as np
import ollama
import requests
from sqlalchemy.orm import Session
from config import settings
import models

EMBED_MODEL = "all-minilm"

class RAGService:
    _cached_embeddings = {}

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """Compute 384-dimensional dense vector embedding using local Ollama model (all-minilm)."""
        cleaned_text = text.strip()[:1500]
        if not cleaned_text:
            return [0.0] * 384

        if cleaned_text in cls._cached_embeddings:
            return cls._cached_embeddings[cleaned_text]

        # 1. Try Ollama Python client
        try:
            client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            res = client.embeddings(model=EMBED_MODEL, prompt=cleaned_text)
            if res and "embedding" in res and res["embedding"]:
                emb = res["embedding"]
                # Normalize vector to unit length
                norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                normalized = [x / norm for x in emb]
                cls._cached_embeddings[cleaned_text] = normalized
                return normalized
        except Exception as e:
            pass

        # 2. Try Ollama REST API fallback
        try:
            resp = requests.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": cleaned_text},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                emb = data.get("embedding", [])
                if emb:
                    norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                    normalized = [x / norm for x in emb]
                    cls._cached_embeddings[cleaned_text] = normalized
                    return normalized
        except Exception as e:
            pass

        # 3. Deterministic word-hash fallback if model not loaded
        vec = [0.0] * 384
        for word in re.findall(r'\b\w+\b', cleaned_text.lower()):
            idx = abs(hash(word)) % 384
            vec[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
        """Split text into semantic chunks with overlap to preserve local context."""
        cleaned = re.sub(r'\s+', ' ', text).strip()
        if not cleaned:
            return []
        
        words = cleaned.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
            i += max(1, chunk_size - overlap)
        return chunks

    @classmethod
    def index_document(cls, db: Session, document_id: int, text: str) -> int:
        """Chunk a document, compute vector embeddings for each chunk, and store in SQLite."""
        # Check if already indexed
        existing_count = db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id == document_id).count()
        if existing_count > 0:
            return existing_count

        chunks = cls.chunk_text(text, chunk_size=300, overlap=60)
        if not chunks:
            chunks = [text[:1000]] if text else ["Empty document."]

        for idx, chunk in enumerate(chunks):
            emb = cls.get_embedding(chunk)
            db_chunk = models.DocumentChunk(
                document_id=document_id,
                chunk_index=idx,
                chunk_text=chunk,
                embedding_json=json.dumps(emb)
            )
            db.add(db_chunk)
        db.commit()
        return len(chunks)

    @classmethod
    def search_document(cls, db: Session, document_id: int, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve top-K most relevant chunks using dense vector cosine similarity matrix multiplication."""
        chunks = db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id == document_id).all()
        if not chunks:
            # Document not yet chunked, chunk it now
            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if doc and doc.extracted_text:
                cls.index_document(db, document_id, doc.extracted_text)
                chunks = db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id == document_id).all()

        if not chunks:
            return []

        # Compute query vector
        query_vec = np.array(cls.get_embedding(query), dtype=np.float32)

        # Build embedding matrix: shape (N, 384)
        matrix = []
        valid_chunks = []
        for c in chunks:
            try:
                emb = json.loads(c.embedding_json)
                matrix.append(emb)
                valid_chunks.append(c)
            except Exception:
                continue

        if not matrix:
            return []

        matrix_np = np.array(matrix, dtype=np.float32)

        # Dot product for all chunks in one matrix operation (N x 384) @ (384,) -> (N,)
        similarities = np.dot(matrix_np, query_vec)

        # Rank indices in descending order of similarity
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices):
            results.append({
                "chunk_id": valid_chunks[idx].id,
                "chunk_index": valid_chunks[idx].chunk_index,
                "text": valid_chunks[idx].chunk_text,
                "score": float(similarities[idx])
            })
        return results

    @staticmethod
    def normalize_query(text: str) -> str:
        """Strip filler conversational phrases to get the core semantic subject."""
        cleaned = re.sub(
            r'^(what is a|what is an|what is|what are|explain|define|tell me about|how does|briefly explain)\s+', 
            '', 
            text.strip(), 
            flags=re.IGNORECASE
        )
        return cleaned.strip(' ?.!').lower()

    @staticmethod
    def normalize_level(level: Optional[str]) -> str:
        """Standardize level tags (e.g. 'Explain Like I\'m 10' and '10 year old' -> '10 year old')."""
        if not level:
            return "general"
        l = level.lower()
        if "10" in l or "child" in l or "kid" in l or "beginner" in l:
            return "10 year old"
        if "college" in l or "student" in l or "intermediate" in l:
            return "college"
        if "expert" in l or "professional" in l or "advanced" in l:
            return "expert"
        return l.strip()

    @classmethod
    def get_semantic_cache(
        cls, 
        db: Session, 
        query: str, 
        module: str, 
        parameters: Optional[str] = None, 
        threshold: float = 0.75
    ) -> Optional[Tuple[str, float]]:
        """
        Check if query matches an existing cached response via vector cosine similarity.
        Returns (response_text, similarity_score) if score >= threshold, else None.
        Sub-50ms instant response!
        """
        norm_level = cls.normalize_level(parameters)
        cache_query = db.query(models.VectorSemanticCache).filter(models.VectorSemanticCache.module == module)
        if parameters:
            cache_query = cache_query.filter(
                (models.VectorSemanticCache.parameters == parameters) |
                (models.VectorSemanticCache.parameters == norm_level)
            )
        
        entries = cache_query.all()
        if not entries:
            # Try without strict parameter filter if none found
            entries = db.query(models.VectorSemanticCache).filter(models.VectorSemanticCache.module == module).all()
        if not entries:
            return None

        clean_q = cls.normalize_query(query)
        query_vec = np.array(cls.get_embedding(clean_q), dtype=np.float32)
        matrix = []
        valid_entries = []
        for e in entries:
            try:
                emb = json.loads(e.embedding_json)
                matrix.append(emb)
                valid_entries.append(e)
            except Exception:
                continue

        if not matrix:
            return None

        matrix_np = np.array(matrix, dtype=np.float32)
        similarities = np.dot(matrix_np, query_vec)
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            hit = valid_entries[best_idx]
            hit.hit_count += 1
            db.commit()
            return hit.response_text, best_score

        return None

    @classmethod
    def set_semantic_cache(
        cls, 
        db: Session, 
        query: str, 
        module: str, 
        parameters: Optional[str], 
        response: str
    ):
        """Save a query embedding and generated response into the semantic cache."""
        clean_q = cls.normalize_query(query)
        norm_level = cls.normalize_level(parameters)
        emb = cls.get_embedding(clean_q)
        cache_item = models.VectorSemanticCache(
            query_text=query.strip(),
            module=module,
            parameters=norm_level,
            embedding_json=json.dumps(emb),
            response_text=response.strip()
        )
        db.add(cache_item)
        db.commit()

    @classmethod
    def seed_knowledge_matrix(cls, db: Session):
        """Pre-populate core concepts into the vector semantic matrix for instant responses."""
        count = db.query(models.VectorSemanticCache).count()
        if count >= 6:
            return

        seeds = [
            {
                "query": "Quantum Computing",
                "module": "explain",
                "params": "Explain Like I'm 10",
                "text": """# 🚀 Quantum Computing (Explained for a 10-Year-Old)

Imagine your normal computer is like a **light switch** that can only be either **ON (1)** or **OFF (0)**. To solve a maze, it has to test one path at a time.

A **Quantum Computer** uses magical rules of nature called **qubits**. Instead of just ON or OFF, a qubit can spin like a coin in mid-air—being both heads and tails at the exact same second! 

### 🌟 The Secret Superpowers:
1. **Superposition**: Testing millions of maze paths at the very same time instead of one by one.
2. **Entanglement**: Two qubits talking to each other instantly, like twin telepathy across the universe!

### 🌍 What Will It Do?
- Invent life-saving medicines in days instead of decades.
- Design unbreakable secret codes for satellites.
- Help self-driving cars solve city traffic instantly."""
            },
            {
                "query": "Quantum Computing",
                "module": "explain",
                "params": "College Student",
                "text": """# ⚛️ Quantum Computing: Foundations & Paradigms

Quantum computing leverages principles of quantum mechanics—primarily **superposition**, **quantum entanglement**, and **interference**—to process complex multidimensional information beyond classical Turing limits.

### 1. Mathematical Formalism
Classical computers represent information in discrete bits $b \\in \\{0, 1\\}$. A quantum bit (qubit) exists in a state space represented as a linear combination (superposition) of basis states:
$$|\\psi\\rangle = \\alpha |0\\rangle + \\beta |1\\rangle$$
where $\\alpha, \\beta \\in \\mathbb{C}$ such that $|\\alpha|^2 + |\\beta|^2 = 1$.

### 2. Quantum Entanglement & Speedup
When multiple qubits become entangled, the state space scales exponentially: $N$ qubits can represent $2^N$ simultaneous quantum amplitudes. Algorithms such as **Shor's Algorithm** (polynomial time integer factorization) and **Grover's Algorithm** (quadratic speedup for unstructured search $\\mathcal{O}(\\sqrt{N})$) demonstrate definitive quantum advantages.

### 3. Engineering Challenges
- **Quantum Decoherence**: Fragility of quantum coherence due to thermal noise and cosmic radiation.
- **Fault-Tolerant Quantum Error Correction (QEC)**: Requires physical-to-logical qubit overheads (typically 1,000 physical qubits per logical qubit)."""
            },
            {
                "query": "Newton's First Law of Motion",
                "module": "explain",
                "params": "Beginner",
                "text": """# 🍎 Newton's First Law of Motion (Law of Inertia)

### 1. Definition
**An object at rest stays at rest, and an object in motion stays in motion with the same speed and in the same direction, unless acted upon by an unbalanced external force.**

### 2. The Core Concept: Inertia
Inertia is the natural tendency of objects to resist any change in their state of motion. The more mass an object has, the more inertia it possesses.

### 3. Everyday Examples:
- **Seatbelts in Cars**: When a car suddenly stops, your body keeps moving forward because of inertia—seatbelts provide the external counter-force!
- **Space Probes**: Spacecraft traveling through deep space keep moving forever without burning fuel because there is no friction or air resistance to slow them down.

### 4. Summary Formula
$$\\sum \\vec{F} = 0 \\implies \\frac{d\\vec{v}}{dt} = 0$$"""
            },
            {
                "query": "Photosynthesis",
                "module": "explain",
                "params": "Beginner",
                "text": """# 🌿 Photosynthesis: The Engine of Life

### 1. Overview
Photosynthesis is the biochemical process by which green plants, algae, and cyanobacteria convert light energy from the sun into chemical energy stored in glucose.

### 2. The Chemical Equation
$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{Light} \\xrightarrow{\\text{Chlorophyll}} \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$

### 3. Two Main Stages:
1. **Light-Dependent Reactions** (Thylakoids): Sunlight excites electrons in chlorophyll, splitting water molecules (photolysis) to generate ATP and NADPH while releasing Oxygen.
2. **The Calvin Cycle / Light-Independent Reactions** (Stroma): Carbon dioxide is fixed into glucose using the energy from ATP and NADPH."""
            }
        ]

        for s in seeds:
            cls.set_semantic_cache(
                db, 
                query=s["query"], 
                module=s["module"], 
                parameters=s.get("params"), 
                response=s["text"]
            )
        print("Vector Semantic Matrix pre-seeded successfully.")
