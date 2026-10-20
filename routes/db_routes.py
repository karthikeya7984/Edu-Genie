from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import get_db
from utils.security import get_current_user

router = APIRouter(prefix="/api/db", tags=["Database Management"])

@router.get("/history")
def get_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.user_id == current_user.id)\
        .order_by(models.ChatHistory.created_at.desc())\
        .all()
    return history

@router.get("/notes", response_model=List[schemas.NoteResponse])
def get_notes(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    notes = db.query(models.SavedNote).filter(models.SavedNote.user_id == current_user.id).all()
    return notes

@router.post("/notes", response_model=schemas.NoteResponse)
def create_note(note: schemas.NoteCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_note = models.SavedNote(user_id=current_user.id, title=note.title, content=note.content)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@router.delete("/notes/{id}")
def delete_note(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    note = db.query(models.SavedNote).filter(models.SavedNote.id == id, models.SavedNote.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"status": "success", "message": "Note deleted successfully"}

@router.get("/bookmarks", response_model=List[schemas.BookmarkResponse])
def get_bookmarks(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    bookmarks = db.query(models.Bookmark).filter(models.Bookmark.user_id == current_user.id).all()
    return bookmarks

@router.post("/bookmarks", response_model=schemas.BookmarkResponse)
def create_bookmark(bookmark: schemas.BookmarkCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if duplicate exists
    existing = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.target_type == bookmark.target_type,
        models.Bookmark.title == bookmark.title
    ).first()
    if existing:
        return existing
        
    new_bookmark = models.Bookmark(
        user_id=current_user.id,
        target_type=bookmark.target_type,
        target_id=bookmark.target_id,
        title=bookmark.title,
        details=bookmark.details
    )
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    return new_bookmark

@router.delete("/bookmarks/{id}")
def delete_bookmark(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    bookmark = db.query(models.Bookmark).filter(models.Bookmark.id == id, models.Bookmark.user_id == current_user.id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"status": "success", "message": "Bookmark removed successfully"}

@router.get("/settings")
def get_settings(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    elif settings.selected_model in ("gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "local-llm", "", None):
        from services.ai_service import DEFAULT_MODEL
        settings.selected_model = DEFAULT_MODEL
        db.commit()
        db.refresh(settings)
    return settings

@router.put("/settings")
def update_settings(settings_data: schemas.SettingsUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = db.query(models.UserSettings).filter(models.UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = models.UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    if settings_data.selected_model is not None:
        settings.selected_model = settings_data.selected_model
    if settings_data.temperature is not None:
        settings.temperature = settings_data.temperature
    if settings_data.max_tokens is not None:
        settings.max_tokens = settings_data.max_tokens
    if settings_data.theme is not None:
        settings.theme = settings_data.theme
    if settings_data.prompt_templates_json is not None:
        settings.prompt_templates_json = settings_data.prompt_templates_json
        
    db.commit()
    db.refresh(settings)
    return settings

@router.post("/feedback")
def submit_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    new_feedback = models.Feedback(
        name=feedback.name,
        email=feedback.email,
        message=feedback.message
    )
    db.add(new_feedback)
    db.commit()
    return {"status": "success", "message": "Thank you for your feedback! We will get back to you shortly."}
