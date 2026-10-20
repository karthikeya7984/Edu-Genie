from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import models
import schemas
from database import get_db
from utils.security import get_current_user
from services.ai_service import EduGenieAI, DEFAULT_MODEL

router = APIRouter(prefix="/api/ai", tags=["AI Modules"])

def save_history(db: Session, user_id: int, module: str, prompt: str, response: str):
    history = models.ChatHistory(user_id=user_id, module=module, prompt=prompt, response=response)
    db.add(history)
    db.commit()

def get_user_ai_params(db: Session, user_id: int):
    settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()
    if not settings:
        return {"model": DEFAULT_MODEL, "temperature": 0.7, "max_tokens": 2048}
    model = settings.selected_model
    if model in ("gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "llama-3.3-70b-versatile", "local-llm", "", None):
        model = DEFAULT_MODEL
    return {
        "model": model,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens
    }

@router.get("/models")
def list_available_models():
    models = EduGenieAI.get_installed_models()
    return {
        "status": "success",
        "provider": "ollama",
        "models": models,
        "default": DEFAULT_MODEL
    }


from fastapi.responses import StreamingResponse
from services.rag_service import RAGService

@router.post("/chat", response_model=schemas.AIResponse)
def chat(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    
    # 1. Check Vector Semantic Cache
    cache_hit = RAGService.get_semantic_cache(db, req.prompt, "chat", threshold=0.92)
    if cache_hit:
        cached_text, score = cache_hit
        enhanced = f"> ⚡ *[Instant Vector Retrieval — Cosine Similarity: {score:.1%}]*\n\n" + cached_text
        save_history(db, current_user.id, "chat", req.prompt, cached_text)
        return {"module": "chat", "data": enhanced}

    # Retrieve last few exchanges for conversation memory
    history_records = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == current_user.id, models.ChatHistory.module == "chat")\
        .order_by(models.ChatHistory.created_at.desc())\
        .limit(3).all()
        
    chat_history = []
    for rec in reversed(history_records):
        chat_history.append({"role": "user", "text": rec.prompt})
        chat_history.append({"role": "assistant", "text": rec.response})
        
    response_text = EduGenieAI.chat(
        prompt=req.prompt,
        history=chat_history,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    
    try:
        RAGService.set_semantic_cache(db, req.prompt, "chat", None, response_text)
    except Exception:
        pass

    save_history(db, current_user.id, "chat", req.prompt, response_text)
    return {"module": "chat", "data": response_text}

@router.post("/stream/chat")
def stream_chat(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    history_records = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == current_user.id, models.ChatHistory.module == "chat")\
        .order_by(models.ChatHistory.created_at.desc())\
        .limit(3).all()
        
    chat_history = []
    for rec in reversed(history_records):
        chat_history.append({"role": "user", "text": rec.prompt})
        chat_history.append({"role": "assistant", "text": rec.response})
        
    return StreamingResponse(
        EduGenieAI.stream_chat(
            prompt=req.prompt,
            history=chat_history,
            temperature=params["temperature"],
            model_name=params["model"],
            db=db,
            user_id=current_user.id
        ),
        media_type="text/event-stream"
    )

@router.post("/qa", response_model=schemas.AIResponse)
def qa(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    
    # Check Vector Semantic Cache
    cache_hit = RAGService.get_semantic_cache(db, req.prompt, "qa", threshold=0.90)
    if cache_hit:
        cached_text, score = cache_hit
        enhanced = f"> ⚡ *[Instant Vector Retrieval — Cosine Similarity: {score:.1%}]*\n\n" + cached_text
        save_history(db, current_user.id, "qa", req.prompt, cached_text)
        return {"module": "qa", "data": enhanced}

    formatted_prompt = f"""Explain this specific topic/question: "{req.prompt}".
    Format your output strictly with the following sections:
    1. **Definition**: Short 2-sentence summary.
    2. **Detailed Explanation**: In-depth concepts.
    3. **Examples**: Code blocks or concrete models.
    4. **Real-world Applications**: Where is this used?
    5. **Common Interview Questions**: 3 relevant interview Q&As."""
    
    response_text = EduGenieAI.chat(
        prompt=formatted_prompt,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    
    try:
        RAGService.set_semantic_cache(db, req.prompt, "qa", None, response_text)
    except Exception:
        pass

    save_history(db, current_user.id, "qa", req.prompt, response_text)
    return {"module": "qa", "data": response_text}

@router.post("/explain", response_model=schemas.AIResponse)
def explain(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    
    # 1. Check Vector Semantic Cache for instant sub-50ms response
    cache_hit = RAGService.get_semantic_cache(db, req.prompt, "explain", req.difficulty, threshold=0.88)
    if cache_hit:
        cached_text, score = cache_hit
        enhanced = f"> ⚡ *[Instant Vector Retrieval Matrix — Cosine Similarity: {score:.1%}]*\n\n" + cached_text
        save_history(db, current_user.id, "explain", f"Concept: {req.prompt} (Level: {req.difficulty})", cached_text)
        return {"module": "explain", "data": enhanced}

    response_text = EduGenieAI.explain_concept(
        concept=req.prompt,
        level=req.difficulty,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    
    # Save to semantic cache
    try:
        RAGService.set_semantic_cache(db, req.prompt, "explain", req.difficulty, response_text)
    except Exception:
        pass

    save_history(db, current_user.id, "explain", f"Concept: {req.prompt} (Level: {req.difficulty})", response_text)
    return {"module": "explain", "data": response_text}

@router.post("/stream/explain")
def stream_explain_route(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    return StreamingResponse(
        EduGenieAI.stream_explain(
            concept=req.prompt,
            level=req.difficulty,
            temperature=params["temperature"],
            model_name=params["model"],
            db=db,
            user_id=current_user.id
        ),
        media_type="text/event-stream"
    )

@router.post("/quiz", response_model=schemas.AIResponse)
def quiz(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    
    # Generate quiz questions (structured as JSON string)
    questions_json = EduGenieAI.generate_quiz(
        topic=req.prompt,
        difficulty=req.difficulty,
        quiz_type=req.quiz_type,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    
    # Save the generated quiz to the database
    new_quiz = models.Quiz(
        topic=req.prompt,
        difficulty=req.difficulty,
        quiz_type=req.quiz_type,
        questions_json=questions_json
    )
    db.add(new_quiz)
    db.commit()
    db.refresh(new_quiz)
    
    save_history(db, current_user.id, "quiz", f"Quiz: {req.prompt} ({req.quiz_type} - {req.difficulty})", questions_json)
    
    # Return both the quiz ID and the raw questions JSON
    import json
    response_payload = {
        "quiz_id": new_quiz.id,
        "questions": json.loads(questions_json)
    }
    
    return {"module": "quiz", "data": json.dumps(response_payload)}

@router.post("/quiz/submit")
def submit_quiz(
    payload: dict = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    quiz_id = payload.get("quiz_id")
    score = payload.get("score")
    total_questions = payload.get("total_questions")
    time_spent = payload.get("time_spent")
    answers = payload.get("answers")
    
    if not quiz_id:
        raise HTTPException(status_code=400, detail="Missing quiz_id")
        
    db_quiz = db.query(models.Quiz).filter(models.Quiz.id == quiz_id).first()
    if not db_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    import json
    result = models.QuizResult(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        total_questions=total_questions,
        time_spent=time_spent,
        answers_json=json.dumps(answers)
    )
    db.add(result)
    db.commit()
    
    return {"status": "success", "message": "Quiz result submitted successfully"}

@router.post("/roadmap", response_model=schemas.AIResponse)
def roadmap(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    response_text = EduGenieAI.generate_roadmap(
        topic=req.prompt,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    
    # Save learning roadmap
    new_roadmap = models.LearningRoadmap(
        user_id=current_user.id,
        topic=req.prompt,
        roadmap_json=response_text
    )
    db.add(new_roadmap)
    db.commit()
    
    save_history(db, current_user.id, "roadmap", req.prompt, response_text)
    return {"module": "roadmap", "data": response_text}

@router.post("/summarize", response_model=schemas.AIResponse)
def summarize(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    
    # difficulty is reused as the summary type here: e.g. "Detailed Summary", "Short Summary"
    summary_type = req.difficulty if req.difficulty else "Detailed Summary"
    response_text = EduGenieAI.summarize(
        text=req.prompt,
        summary_type=summary_type,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    save_history(db, current_user.id, "summarize", f"Summarize text ({len(req.prompt)} chars)", response_text)
    return {"module": "summarize", "data": response_text}

@router.post("/homework", response_model=schemas.AIResponse)
def homework(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    response_text = EduGenieAI.solve_homework(
        problem_text=req.prompt,
        context_details=req.context,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    save_history(db, current_user.id, "homework", req.prompt, response_text)
    return {"module": "homework", "data": response_text}

@router.post("/flashcards", response_model=schemas.AIResponse)
def flashcards(req: schemas.AIPrompt, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    params = get_user_ai_params(db, current_user.id)
    response_text = EduGenieAI.generate_flashcards(
        topic=req.prompt,
        difficulty=req.difficulty,
        temperature=params["temperature"],
        model_name=params["model"]
    )
    save_history(db, current_user.id, "flashcards", f"Flashcards for: {req.prompt}", response_text)
    return {"module": "flashcards", "data": response_text}
