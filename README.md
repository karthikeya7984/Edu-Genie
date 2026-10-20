# EduGenie - Learn Smarter with AI

EduGenie is a production-ready, AI-powered educational SaaS platform designed to assist students, teachers, self-learners, and competitive exam aspirants. Utilizing Google Gemini API for natural language processing, EduGenie features interactive Q&A solving, custom quiz generation, concept simplification, flashcard creation, textbook summarizers, and master learning roadmaps.

The project is structured with a modular **FastAPI** backend and an advanced, responsive glassmorphic **Single Page Application (SPA)** dashboard.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JS (SPA State Architecture), Particles.js, Font Awesome, Bootstrap 5, Chart.js.
- **Backend**: Python, FastAPI, SQLAlchemy ORM, Pydantic v2, JWT Security, Jinja2 Templates.
- **AI Integration**: **Local Ollama** (llama3.2 / llama3.1 / mistral) with zero cloud API keys, plus optional Groq cloud fallback.
- **Deployment**: Windows Command Prompt / PowerShell, Docker, SQLite.

---

## 🚀 How to Run the Application Using Command Prompt (cmd)

### 1. Ensure Ollama is Running
If you already have Ollama installed, it is typically running in the system tray. If not, open a Command Prompt and start it:
```cmd
ollama serve
```
Make sure you have the `llama3.2` model downloaded (or any model of your choice):
```cmd
ollama pull llama3.2
```

### 2. Open Command Prompt and Navigate to the Project
```cmd
cd c:\Users\chkar\OneDrive\Documents\Edu-Genie
```

### 3. Install Dependencies (First Time Only)
```cmd
pip install -r requirements.txt
```

### 4. Start the EduGenie Application
Run the following command to start the server:
```cmd
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
*(Or simply `uvicorn main:app --reload`)*

### 5. Open in Your Browser
- **Web Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Pre-seeded Accounts (For Testing & Demo)

To make testing instant, the database is pre-seeded with two accounts:

1. **Student Account** (Standard Dashboard access)
   - **Email**: `demo@edugenie.com`
   - **Password**: `password123`
2. **Admin Account** (Includes Admin Panel link with Charts and audit logs)
   - **Email**: `admin@edugenie.com`
   - **Password**: `admin123`
*(Or click the **1-Click Quick Demo Login** button on the home page).*
