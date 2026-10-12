"""
EduPulse AI - One-Click Launcher
KPMG Challenge 04: AI-Powered Student Analytics and Success Platform
"""
import sys
import os

# Set UTF-8 encoding for Windows console compatibility
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("=" * 70)
    print("[*] EduPulse AI - AI-Powered Student Analytics & Success Platform")
    print("    KPMG in India - Challenge 04 Solution")
    print("=" * 70)

    # 1. Ensure working directory is project root
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # 2. Check / Generate Synthetic Database
    db_path = os.path.join(project_dir, "app", "data", "students_db.json")
    if not os.path.exists(db_path):
        print("\n[Step 1/3] Generating synthetic cohort of 360 students...")
        from app.data.generator import save_default_dataset
        save_default_dataset(db_path)
    else:
        print("\n[Step 1/3] Found existing student database.")

    # 3. Train predictive ML model
    print("\n[Step 2/3] Initializing Predictive Risk Engine & Explainable AI (XAI)...")
    from app.routers.api import get_students
    from app.ml.model import predictor
    students = get_students()
    print(f"Loaded {len(students)} student records.")
    if not predictor.is_trained:
        predictor.train_on_students(students)

    # 4. Launch FastAPI server
    print("\n[Step 3/3] Starting EduPulse AI Server at http://127.0.0.1:8000 ...")
    print("=" * 70)
    print(">> Open your browser and navigate to: http://127.0.0.1:8000")
    print(">> Interactive API Docs available at: http://127.0.0.1:8000/docs")
    print("=" * 70)

    try:
        import uvicorn
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\nShutting down EduPulse AI gracefully. Good luck with your hackathon!")

if __name__ == "__main__":
    main()
