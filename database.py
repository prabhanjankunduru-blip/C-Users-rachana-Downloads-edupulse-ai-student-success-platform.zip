import sqlite3
import os
import json
from typing import List, Dict, Any, Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, "students_platform.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table (for authentication)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        display_name TEXT NOT NULL,
        license TEXT,
        role TEXT DEFAULT 'student',
        email TEXT,
        roll_no TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Students profile table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        department TEXT NOT NULL,
        branch TEXT NOT NULL,
        section TEXT NOT NULL,
        institution TEXT NOT NULL,
        year INTEGER DEFAULT 2,
        semester INTEGER DEFAULT 3,
        avatar_color TEXT DEFAULT '#2563EB'
    )
    """)

    # 3. Academic Metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_metrics (
        student_id TEXT PRIMARY KEY,
        current_gpa REAL,
        prior_gpa REAL,
        gpa_delta REAL,
        sem1_gpa REAL,
        sem2_gpa REAL,
        sem3_gpa REAL,
        credits_completed INTEGER,
        total_credits INTEGER,
        backlogs INTEGER DEFAULT 0,
        class_rank INTEGER,
        total_students INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 4. Attendance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        student_id TEXT PRIMARY KEY,
        attendance_rate REAL,
        lab_attendance REAL,
        theory_attendance REAL,
        total_classes INTEGER,
        attended_classes INTEGER,
        medical_leaves INTEGER DEFAULT 0,
        condonation_required BOOLEAN DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 5. LMS Data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lms_data (
        student_id TEXT PRIMARY KEY,
        weekly_logins INTEGER,
        assignment_submission_rate REAL,
        modules_completed INTEGER,
        total_modules INTEGER,
        video_watch_hours REAL,
        forum_posts INTEGER,
        avg_quiz_score REAL,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 6. Student Engagement
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS engagement (
        student_id TEXT PRIMARY KEY,
        participation_score REAL,
        extracurricular_score REAL,
        club_memberships INTEGER,
        hackathons_attended INTEGER,
        workshops_attended INTEGER,
        wellbeing_score INTEGER,
        sentiment TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 7. Placements & Career Readiness
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS placements (
        student_id TEXT PRIMARY KEY,
        eligibility_status TEXT,
        readiness_score REAL,
        mock_interview_score REAL,
        coding_score REAL,
        resume_ats_score REAL,
        target_domain TEXT,
        dream_companies TEXT,
        offers_count INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 8. Skills Matrix
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        student_id TEXT PRIMARY KEY,
        dsa_score REAL,
        web_dev_score REAL,
        ai_ml_score REAL,
        cloud_score REAL,
        soft_skills_score REAL,
        problem_solving_score REAL,
        top_skill TEXT,
        recommended_upskill TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 9. Faculty / Lecture Feedback
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        course_code TEXT,
        course_name TEXT,
        faculty_name TEXT,
        rating REAL,
        pedagogy_rating REAL,
        clarity_rating REAL,
        pace_rating REAL,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 10. Semester Exam Results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        semester TEXT,
        course_code TEXT,
        course_name TEXT,
        credits INTEGER,
        internal_marks REAL,
        external_marks REAL,
        total_marks REAL,
        grade TEXT,
        grade_points REAL,
        status TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 11. Re-corrections / Revaluation Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recorrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        course_code TEXT,
        course_name TEXT,
        semester TEXT,
        original_marks REAL,
        original_grade TEXT,
        revised_marks REAL,
        revised_grade TEXT,
        request_type TEXT DEFAULT 'Revaluation',
        reason TEXT,
        fee_amount REAL DEFAULT 500,
        fee_paid BOOLEAN DEFAULT 1,
        status TEXT DEFAULT 'Under Review',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 12. Fee Payments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        fee_type TEXT,
        title TEXT,
        amount REAL,
        due_date TEXT,
        status TEXT, -- Paid, Pending, Overdue
        transaction_id TEXT,
        payment_date TEXT,
        payment_method TEXT,
        invoice_number TEXT UNIQUE,
        receipt_url TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    # 13. Risk Assessment & Success Score
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_success (
        student_id TEXT PRIMARY KEY,
        success_score REAL,
        percentile REAL,
        tier TEXT,
        risk_level TEXT,
        dropout_probability REAL,
        top_risk_factors TEXT,
        academic_weight REAL,
        attendance_weight REAL,
        lms_weight REAL,
        skills_weight REAL,
        engagement_weight REAL,
        last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Initialized SQLite database schema successfully!")
