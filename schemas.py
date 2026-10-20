from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserProfileResponse(BaseModel):
    name: str
    email: str
    role: str
    joined: datetime
    photo_url: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    achievements: Optional[str] = None
    certificates: Optional[str] = None
    learning_streak: int

    class Config:
        from_attributes = True

class UserProfileUpdate(BaseModel):
    photo_url: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None
    achievements: Optional[str] = None
    certificates: Optional[str] = None

class AIPrompt(BaseModel):
    prompt: str
    context: Optional[str] = None
    difficulty: Optional[str] = "Medium"
    quiz_type: Optional[str] = "MCQs"

class AIResponse(BaseModel):
    module: str
    data: str

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class BookmarkCreate(BaseModel):
    target_type: str
    target_id: Optional[int] = None
    title: str
    details: Optional[str] = None

class BookmarkResponse(BaseModel):
    id: int
    target_type: str
    target_id: Optional[int] = None
    title: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackCreate(BaseModel):
    name: str
    email: EmailStr
    message: str

class SettingsUpdate(BaseModel):
    selected_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    theme: Optional[str] = None
    prompt_templates_json: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    char_count: int
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailResponse(DocumentResponse):
    extracted_text: str

class DocumentQARequest(BaseModel):
    question: str

class DocumentQuizRequest(BaseModel):
    difficulty: Optional[str] = "Medium"
    quiz_type: Optional[str] = "MCQs"
    num_questions: Optional[int] = 5

class DocumentFlashcardsRequest(BaseModel):
    num_cards: Optional[int] = 5

class DocumentSummarizeRequest(BaseModel):
    summary_type: Optional[str] = "Comprehensive"

