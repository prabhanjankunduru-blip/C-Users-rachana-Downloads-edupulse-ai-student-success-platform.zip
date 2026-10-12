from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3
from app.db.database import get_connection

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    roll_no: str
    name: str
    email: str
    password: str
    section: Optional[str] = "Section A"
    phone: Optional[str] = "+91 9876543210"

@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    
    clean_u = req.username.strip()
    clean_p = req.password.strip()

    # Search by username, email, or roll_no
    cursor.execute("""
    SELECT u.*, s.department, s.avatar_color 
    FROM users u
    LEFT JOIN students s ON u.roll_no = s.roll_no
    WHERE (LOWER(u.username) = LOWER(?) OR LOWER(u.email) = LOWER(?) OR LOWER(u.roll_no) = LOWER(?))
    """, (clean_u, clean_u, clean_u))
    
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or institutional email.")
        
    if user["password"] != clean_p:
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect password. Please verify your Microsoft 365 / portal credentials.")
        
    role = user["role"]
    roll_no = user["roll_no"]
    display_name = user["display_name"]
    email = user["email"]
    dept = user["department"] or "Computer Science & Engineering"
    avatar = user["avatar_color"] or "#2563EB"
    
    conn.close()
    
    return {
        "success": True,
        "token": f"session_token_{roll_no or 'ADMIN'}",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": display_name,
            "role": role,
            "roll_no": roll_no,
            "email": email,
            "license": user["license"],
            "department": dept,
            "avatar_color": avatar
        }
    }

@router.post("/register")
def register(req: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()

    roll_no = req.roll_no.strip().upper()
    email = req.email.strip().lower()

    # Check existing
    cursor.execute("SELECT id FROM users WHERE roll_no = ? OR email = ?", (roll_no, email))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student with this Roll Number or Email already exists!")

    # Insert into users
    cursor.execute("""
    INSERT INTO users (id, username, password, display_name, license, role, email, roll_no)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        roll_no,
        email,
        req.password.strip(),
        req.name.strip(),
        "Microsoft 365 A3 for students use benefit",
        "student",
        email,
        roll_no
    ))

    # Insert into students
    cursor.execute("""
    INSERT INTO students (id, roll_no, name, email, phone, department, branch, section, institution, year, semester, avatar_color)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        roll_no,
        roll_no,
        req.name.strip(),
        email,
        req.phone.strip(),
        f"CSE - {req.section}",
        "Computer Science & Engineering",
        req.section,
        "St. Mary's Group of Institutions",
        2,
        3,
        "#059669"
    ))

    # Initialize basic academic metrics & success score
    cursor.execute("""
    INSERT INTO academic_metrics (student_id, current_gpa, prior_gpa, gpa_delta, sem1_gpa, sem2_gpa, sem3_gpa, credits_completed, total_credits, backlogs, class_rank, total_students)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, 8.2, 8.0, 0.2, 7.9, 8.0, 8.2, 64, 160, 0, 45, 199))

    cursor.execute("""
    INSERT INTO attendance (student_id, attendance_rate, lab_attendance, theory_attendance, total_classes, attended_classes, medical_leaves, condonation_required)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, 88.5, 92.0, 86.0, 180, 159, 1, 0))

    cursor.execute("""
    INSERT INTO lms_data (student_id, weekly_logins, assignment_submission_rate, modules_completed, total_modules, video_watch_hours, forum_posts, avg_quiz_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, 12, 90.0, 9, 10, 24.5, 6, 85.0))

    cursor.execute("""
    INSERT INTO engagement (student_id, participation_score, extracurricular_score, club_memberships, hackathons_attended, workshops_attended, wellbeing_score, sentiment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, 85.0, 80.0, 2, 2, 2, 8, "Positive"))

    cursor.execute("""
    INSERT INTO placements (student_id, eligibility_status, readiness_score, mock_interview_score, coding_score, resume_ats_score, target_domain, dream_companies, offers_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, "Eligible - Premium Tier", 85.0, 82.0, 84.0, 88.0, "Full Stack Development", "Google, TCS, KPMG", 0))

    cursor.execute("""
    INSERT INTO skills (student_id, dsa_score, web_dev_score, ai_ml_score, cloud_score, soft_skills_score, problem_solving_score, top_skill, recommended_upskill)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, 82.0, 85.0, 78.0, 75.0, 88.0, 84.0, "Full-Stack Development", "Cloud Architecture"))

    cursor.execute("""
    INSERT INTO student_success (student_id, success_score, percentile, tier, risk_level, dropout_probability, top_risk_factors, academic_weight, attendance_weight, lms_weight, skills_weight, engagement_weight)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        roll_no, 84.5, 82.0, "Competent Scholar", "Low", 8.5,
        '["Strong foundational consistency across LMS and exams"]', 35.0, 25.0, 15.0, 15.0, 10.0
    ))

    # Fee dues
    cursor.execute("""
    INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, invoice_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, "Exam Fee", "End Semester Examination Fee (Sem 3)", 2500.0, "2026-11-15", "Pending", f"INV-EXM-NEW-{roll_no}"))

    cursor.execute("""
    INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, invoice_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (roll_no, "Tuition Fee", "B.Tech Computer Science Academic Tuition", 65000.0, "2026-10-10", "Pending", f"INV-TUI-NEW-{roll_no}"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Student registration completed successfully! You can now sign in.",
        "roll_no": roll_no,
        "email": email
    }

@router.get("/demo-users")
def get_demo_users():
    """Provides one-click demo credentials for immediate testing"""
    return [
        {
            "label": "Dean / Executive Advisor",
            "username": "admin@stmarysgroup.com",
            "password": "admin123",
            "role": "Institutional Dean",
            "badge": "Advisor Dashboard"
        },
        {
            "label": "Rohith Yanamalla (Top Performer)",
            "username": "25D01A05F1@stmarysgroup.com",
            "password": "Y$548911956538al",
            "role": "Elite Vanguard Student (GPA: 9.45)",
            "badge": "Low Risk"
        },
        {
            "label": "Sathish Dasoju (At-Risk Intervention)",
            "username": "25D01A0506@stmarysgroup.com",
            "password": "D@418102817943ux",
            "role": "High Risk Student (Attendance: 62%)",
            "badge": "Early Warning"
        },
        {
            "label": "Ankitha Ajemera (Active Student)",
            "username": "25D01A0501@stmarysgroup.com",
            "password": "C!054379597796ob",
            "role": "Section A Student (GPA: 8.2)",
            "badge": "Competent Scholar"
        }
    ]
