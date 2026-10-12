import os
import sys

# Ensure parent directory containing 'app' package is always in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.api import router as api_router, get_students
from app.routers.analytics import router as analytics_router
from app.routers.auth import router as auth_router
from app.routers.copilot import router as copilot_router
from app.routers.fees import router as fees_router
from app.routers.results import router as results_router
from app.ml.model import predictor

app = FastAPI(
    title="EduPulse AI - Student Analytics & Success Platform",
    description="KPMG Challenge 04: AI-Powered Institutional Intelligence, Early Risk Warning & Prescriptive Success Interventions",
    version="1.0.0"
)

# Enable CORS for open integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(api_router)
app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(copilot_router)
app.include_router(fees_router)
app.include_router(results_router)

# Mount Static Assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    print("Initializing EduPulse AI Engine...")
    # Seed data & train baseline predictor
    students = get_students()
    print(f"Loaded {len(students)} student profiles into institutional knowledge base.")

@app.get("/")
def serve_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "EduPulse AI Backend Active. Static dashboard loading..."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
