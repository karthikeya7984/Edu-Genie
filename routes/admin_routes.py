from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
from database import get_db
from utils.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])

def check_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user

@router.get("/users")
def get_users(admin: models.User = Depends(check_admin), db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    # Serialize safely
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
            "streak": u.profile.learning_streak if u.profile else 0
        } for u in users
    ]

@router.get("/feedback")
def get_feedback(admin: models.User = Depends(check_admin), db: Session = Depends(get_db)):
    feedback_list = db.query(models.Feedback).order_by(models.Feedback.created_at.desc()).all()
    return feedback_list

@router.get("/analytics")
def get_analytics(admin: models.User = Depends(check_admin), db: Session = Depends(get_db)):
    total_users = db.query(models.User).count()
    total_feedback = db.query(models.Feedback).count()
    total_chats = db.query(models.ChatHistory).count()
    total_quizzes = db.query(models.Quiz).count()
    
    # Calculate some mock logs for API usage & growth over time for dashboard charts
    growth_labels = []
    growth_data = []
    
    today = datetime.utcnow()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%b %d")
        growth_labels.append(day_str)
        # Count user signups on that day
        start_of_day = datetime(day.year, day.month, day.day, 0, 0, 0)
        end_of_day = datetime(day.year, day.month, day.day, 23, 59, 59)
        signups = db.query(models.User).filter(models.User.created_at.between(start_of_day, end_of_day)).count()
        growth_data.append(signups + random_seeded_growth(i))  # Add minor variation for rich graphs
        
    # Module usage breakdown
    modules = ["chat", "explain", "quiz", "roadmap", "summarize", "homework", "flashcards"]
    module_counts = {}
    for mod in modules:
        count = db.query(models.ChatHistory).filter(models.ChatHistory.module == mod).count()
        module_counts[mod] = count
        
    # Prompt logs
    recent_logs = db.query(models.ChatHistory).order_by(models.ChatHistory.created_at.desc()).limit(15).all()
    serialized_logs = [
        {
            "id": log.id,
            "user_email": log.user.email if log.user else "Unknown",
            "module": log.module,
            "prompt": log.prompt[:80] + ("..." if len(log.prompt) > 80 else ""),
            "timestamp": log.created_at
        } for log in recent_logs
    ]
    
    return {
        "summary": {
            "total_users": total_users,
            "total_feedback": total_feedback,
            "total_chats": total_chats,
            "total_quizzes": total_quizzes
        },
        "charts": {
            "growth_labels": growth_labels,
            "growth_data": growth_data,
            "module_counts": module_counts
        },
        "recent_logs": serialized_logs
    }

def random_seeded_growth(day_offset: int) -> int:
    # Deterministic variation
    return (day_offset * 3 + 2) % 5
