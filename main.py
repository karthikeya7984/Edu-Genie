from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from routes import auth_routes, ai_routes, db_routes, admin_routes, document_routes
from utils.security import get_password_hash
import models
import os

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EduGenie", description="AI-Powered Educational Assistant")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Static and Templates configuration
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Register Routers
app.include_router(auth_routes.router)
app.include_router(ai_routes.router)
app.include_router(db_routes.router)
app.include_router(admin_routes.router)
app.include_router(document_routes.router)

@app.on_event("startup")
def startup_seeding():
    db = SessionLocal()
    try:
        # Seed standard demo student
        demo_email = "demo@edugenie.com"
        demo_user = db.query(models.User).filter(models.User.email == demo_email).first()
        if not demo_user:
            hashed_pwd = get_password_hash("password123")
            demo_user = models.User(name="Alex Learner", email=demo_email, hashed_password=hashed_pwd, role="student")
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            
            # Setup profile
            profile = models.UserProfile(user_id=demo_user.id, education="University Student", skills="Python, Web Dev", achievements="3-Day Learning Streak", learning_streak=3)
            db.add(profile)
            # Setup default settings
            settings = models.UserSettings(user_id=demo_user.id)
            db.add(settings)
            db.commit()
            print("Demo user created.")

        # Seed admin
        admin_email = "admin@edugenie.com"
        admin_user = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin_user:
            hashed_pwd = get_password_hash("admin123")
            admin_user = models.User(name="System Admin", email=admin_email, hashed_password=hashed_pwd, role="admin")
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Setup profile
            profile = models.UserProfile(user_id=admin_user.id, education="Tech Architect", skills="Databases, Security", achievements="Superuser Access", learning_streak=1)
            db.add(profile)
            # Setup settings
            settings = models.UserSettings(user_id=admin_user.id)
            db.add(settings)
            db.commit()
            print("Admin user created.")
            
        # Seed RAG Vector Semantic Knowledge Matrix
        try:
            from services.rag_service import RAGService
            RAGService.seed_knowledge_matrix(db)
        except Exception as e:
            print(f"RAG matrix seeding notice: {e}")
            
    finally:
        db.close()

# Frontend view routing
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Global error page handlers (404 and 500)
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("index.html", {"request": request, "error_code": 404, "error_msg": "Page Not Found"}, status_code=404)

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("index.html", {"request": request, "error_code": 500, "error_msg": "Internal Server Error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
