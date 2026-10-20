from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="student")  # student, teacher, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("LearningRoadmap", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("SavedNote", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    photo_url = Column(String, nullable=True)
    education = Column(String, nullable=True)
    skills = Column(String, nullable=True)        # comma separated or json
    achievements = Column(String, nullable=True)  # comma separated or json
    certificates = Column(String, nullable=True)  # JSON list
    learning_streak = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profile")

class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module = Column(String)  # chat, explain, qa, homework, summarizer
    prompt = Column(Text)
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_histories")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    difficulty = Column(String)  # Easy, Medium, Hard
    quiz_type = Column(String)   # MCQs, True/False, Fill in the blanks
    questions_json = Column(Text)  # Store JSON representation of quiz
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship("QuizResult", back_populates="quiz", cascade="all, delete")

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    score = Column(Integer)
    total_questions = Column(Integer)
    time_spent = Column(Integer)  # in seconds
    answers_json = Column(Text)   # JSON string of user answers
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="results")

class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String, index=True)
    roadmap_json = Column(Text)  # Store JSON roadmap
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="roadmaps")

class SavedNote(Base):
    __tablename__ = "saved_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_type = Column(String)  # chat, quiz, roadmap, note
    target_id = Column(Integer, nullable=True)
    title = Column(String)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    selected_model = Column(String, default="llama3.2")  # Ollama: llama3.2
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    prompt_templates_json = Column(Text, nullable=True)  # Customized templates
    theme = Column(String, default="dark")  # dark, light
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="settings")
 
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, index=True)
    file_type = Column(String)  # pdf, docx, txt, md
    file_size = Column(Integer)  # bytes
    char_count = Column(Integer, default=0)
    extracted_text = Column(Text)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    chunk_text = Column(Text)
    embedding_json = Column(Text)  # JSON-serialized vector embedding
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")

class VectorSemanticCache(Base):
    __tablename__ = "vector_semantic_cache"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String, index=True)
    module = Column(String, index=True)  # "explain", "qa", "chat"
    parameters = Column(String, nullable=True)  # e.g. "Explain Like I'm 10"
    embedding_json = Column(Text)  # Vector embedding for cosine search
    response_text = Column(Text)
    hit_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

