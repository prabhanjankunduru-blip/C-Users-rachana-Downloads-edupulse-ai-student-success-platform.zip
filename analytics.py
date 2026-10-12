from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from app.db.database import get_connection

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/overview")
def get_institutional_overview():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()["total"]

    cursor.execute("""
    SELECT 
        AVG(am.current_gpa) as avg_gpa,
        AVG(att.attendance_rate) as avg_att,
        AVG(lms.assignment_submission_rate) as avg_assign,
        AVG(ss.success_score) as avg_success
    FROM academic_metrics am
    JOIN attendance att ON am.student_id = att.student_id
    JOIN lms_data lms ON am.student_id = lms.student_id
    JOIN student_success ss ON am.student_id = ss.student_id
    """)
    macro = cursor.fetchone()

    # Risk counts
    cursor.execute("SELECT risk_level, COUNT(*) as count FROM student_success GROUP BY risk_level")
    risk_rows = cursor.fetchall()
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    for r in risk_rows:
        if r["risk_level"] in risk_counts:
            risk_counts[r["risk_level"]] = r["count"]

    # Section breakdown
    cursor.execute("""
    SELECT 
        s.section,
        COUNT(s.id) as total,
        AVG(am.current_gpa) as avg_gpa,
        AVG(att.attendance_rate) as avg_att,
        SUM(CASE WHEN ss.risk_level = 'High' THEN 1 ELSE 0 END) as high_risk_count
    FROM students s
    JOIN academic_metrics am ON s.id = am.student_id
    JOIN attendance att ON s.id = att.student_id
    JOIN student_success ss ON s.id = ss.student_id
    GROUP BY s.section
    """)
    sections = [dict(row) for row in cursor.fetchall()]

    # Fee status summary
    cursor.execute("""
    SELECT status, COUNT(*) as count, SUM(amount) as total_amount 
    FROM fee_payments 
    GROUP BY status
    """)
    fee_rows = [dict(row) for row in cursor.fetchall()]

    # At-risk students list (top 5 priority)
    cursor.execute("""
    SELECT s.id, s.name, s.department, am.current_gpa, att.attendance_rate, ss.risk_level, ss.dropout_probability, ss.top_risk_factors
    FROM students s
    JOIN academic_metrics am ON s.id = am.student_id
    JOIN attendance att ON s.id = att.student_id
    JOIN student_success ss ON s.id = ss.student_id
    WHERE ss.risk_level = 'High'
    ORDER BY ss.dropout_probability DESC
    LIMIT 6
    """)
    at_risk_preview = []
    for r in cursor.fetchall():
        d = dict(r)
        d["top_risk_factors"] = json.loads(d["top_risk_factors"]) if d["top_risk_factors"] else []
        at_risk_preview.append(d)

    conn.close()

    return {
        "kpis": {
            "total_students": total_students,
            "high_risk_count": risk_counts["High"],
            "high_risk_pct": round((risk_counts["High"] / max(1, total_students)) * 100, 1),
            "medium_risk_count": risk_counts["Medium"],
            "low_risk_count": risk_counts["Low"],
            "avg_gpa": round(macro["avg_gpa"] or 0.0, 2),
            "avg_attendance": round(macro["avg_att"] or 0.0, 1),
            "avg_assignment_compliance": round(macro["avg_assign"] or 0.0, 1),
            "institutional_success_index": round(macro["avg_success"] or 0.0, 1)
        },
        "sections": sections,
        "fee_summary": fee_rows,
        "priority_interventions": at_risk_preview
    }

@router.get("/students")
def get_students_directory(
    search: Optional[str] = None,
    risk: Optional[str] = "All",
    section: Optional[str] = "All",
    fee_status: Optional[str] = "All"
):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        s.id, s.roll_no, s.name, s.email, s.department, s.section, s.avatar_color,
        am.current_gpa, am.gpa_delta, am.class_rank,
        att.attendance_rate,
        ss.success_score, ss.risk_level, ss.dropout_probability, ss.tier
    FROM students s
    JOIN academic_metrics am ON s.id = am.student_id
    JOIN attendance att ON s.id = att.student_id
    JOIN student_success ss ON s.id = ss.student_id
    WHERE 1=1
    """
    params = []

    if search:
        s_clean = f"%{search.strip().lower()}%"
        query += " AND (LOWER(s.name) LIKE ? OR LOWER(s.roll_no) LIKE ? OR LOWER(s.email) LIKE ?)"
        params.extend([s_clean, s_clean, s_clean])

    if risk and risk != "All":
        query += " AND ss.risk_level = ?"
        params.append(risk)

    if section and section != "All":
        query += " AND s.section = ?"
        params.append(section)

    query += " ORDER BY am.class_rank ASC"
    
    cursor.execute(query, params)
    students = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "count": len(students),
        "students": students
    }

@router.get("/student/{student_id}")
def get_student_profile(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ? OR roll_no = ?", (student_id, student_id))
    s_base = cursor.fetchone()
    if not s_base:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    sid = s_base["id"]

    cursor.execute("SELECT * FROM academic_metrics WHERE student_id = ?", (sid,))
    acad = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM attendance WHERE student_id = ?", (sid,))
    att = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM lms_data WHERE student_id = ?", (sid,))
    lms = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM engagement WHERE student_id = ?", (sid,))
    eng = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM placements WHERE student_id = ?", (sid,))
    placements = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM skills WHERE student_id = ?", (sid,))
    skills = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM student_success WHERE student_id = ?", (sid,))
    ss_row = cursor.fetchone()
    ss = dict(ss_row or {})
    if ss.get("top_risk_factors"):
        ss["top_risk_factors"] = json.loads(ss["top_risk_factors"])

    # Results
    cursor.execute("SELECT * FROM exam_results WHERE student_id = ?", (sid,))
    results = [dict(r) for r in cursor.fetchall()]

    # Fees
    cursor.execute("SELECT * FROM fee_payments WHERE student_id = ?", (sid,))
    fees = [dict(r) for r in cursor.fetchall()]

    # Re-corrections
    cursor.execute("SELECT * FROM recorrections WHERE student_id = ?", (sid,))
    recorrections = [dict(r) for r in cursor.fetchall()]

    # Feedback submitted
    cursor.execute("SELECT * FROM faculty_feedback WHERE student_id = ?", (sid,))
    feedback = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "profile": dict(s_base),
        "academic": acad,
        "attendance": att,
        "lms": lms,
        "engagement": eng,
        "placements": placements,
        "skills": skills,
        "success_score": ss,
        "results": results,
        "fees": fees,
        "recorrections": recorrections,
        "feedback": feedback
    }

# 1. ACADEMIC MODULE
@router.get("/academic/{student_id}")
def get_academic_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM academic_metrics WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student metrics not found")

    metrics = dict(row)
    cursor.execute("SELECT * FROM exam_results WHERE student_id = ?", (student_id,))
    courses = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "metrics": metrics,
        "semester_trajectory": [
            {"semester": "Sem 1", "gpa": metrics["sem1_gpa"]},
            {"semester": "Sem 2", "gpa": metrics["sem2_gpa"]},
            {"semester": "Sem 3 (Current)", "gpa": metrics["sem3_gpa"]}
        ],
        "course_performance": courses,
        "bottlenecks": [c for c in courses if c["total_marks"] < 60 or c["course_code"] in ["CS301", "MA301"]]
    }

# 2. ATTENDANCE MODULE
@router.get("/attendance/{student_id}")
def get_attendance_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendance WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Attendance not found")

    att = dict(row)
    # Generate weekly trend
    base = att["attendance_rate"]
    weekly_trend = [
        {"week": "Week 1", "rate": round(min(100.0, base - 3.2), 1)},
        {"week": "Week 2", "rate": round(min(100.0, base - 1.5), 1)},
        {"week": "Week 3", "rate": round(min(100.0, base + 2.0), 1)},
        {"week": "Week 4", "rate": round(min(100.0, base + 0.5), 1)},
        {"week": "Week 5", "rate": round(min(100.0, base - 0.8), 1)},
        {"week": "Week 6 (Current)", "rate": base}
    ]
    conn.close()

    return {
        "details": att,
        "statutory_threshold": 75.0,
        "shortage_alert": att["attendance_rate"] < 75.0,
        "classes_needed_for_75": max(0, int((0.75 * att["total_classes"] - att["attended_classes"]) / 0.25)) if att["attendance_rate"] < 75.0 else 0,
        "weekly_trend": weekly_trend
    }

# 3. LMS MODULE
@router.get("/lms/{student_id}")
def get_lms_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lms_data WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="LMS data not found")

    lms = dict(row)
    conn.close()

    return {
        "details": lms,
        "modules_progress": [
            {"module": "Unit 1: Advanced Trees & Graphs", "progress": 100, "status": "Completed"},
            {"module": "Unit 2: Dynamic Programming & Greedy Algorithms", "progress": int(lms["assignment_submission_rate"]), "status": "In Progress"},
            {"module": "Unit 3: Operating System Kernel Threads", "progress": 85, "status": "Completed"},
            {"module": "Unit 4: Relational Query Optimization", "progress": 60, "status": "In Progress"},
            {"module": "Unit 5: Discrete Probability & Graph Theory", "progress": int(lms["assignment_submission_rate"] * 0.8), "status": "Pending Review"}
        ]
    }

# 4. ENGAGEMENT MODULE
@router.get("/engagement/{student_id}")
def get_engagement_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM engagement WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Engagement data not found")

    eng = dict(row)
    conn.close()

    return {
        "details": eng,
        "activities": [
            {"title": "KPMG Ideation Challenge 2026", "category": "Hackathon", "status": "Participated"},
            {"title": "Google Developer Student Club (GDSC)", "category": "Technical Club", "status": "Active Member"},
            {"title": "AWS Cloud Foundations Bootcamp", "category": "Workshop", "status": "Certified"}
        ]
    }

# 5. PLACEMENTS MODULE
@router.get("/placements/{student_id}")
def get_placements_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM placements WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Placements data not found")

    plc = dict(row)
    conn.close()

    return {
        "details": plc,
        "readiness_breakdown": {
            "Aptitude & Logical Reasoning": round(plc["readiness_score"] * 0.96, 1),
            "Technical Coding Assessment": plc["coding_score"],
            "System Design & Core CS": round(plc["mock_interview_score"] * 0.92, 1),
            "HR & Soft Skills Interview": plc["mock_interview_score"],
            "Resume ATS Optimization": plc["resume_ats_score"]
        },
        "upcoming_campus_drives": [
            {"company": "KPMG India", "role": "Associate Technology Consultant", "package": "₹9.5 LPA", "date": "2026-11-20", "eligibility": "Met"},
            {"company": "Google Cloud", "role": "Cloud Solutions Associate", "package": "₹14.0 LPA", "date": "2026-12-05", "eligibility": "Met" if plc["readiness_score"] >= 85 else "Review Needed"},
            {"company": "TCS Digital", "role": "Systems Engineer", "package": "₹7.5 LPA", "date": "2026-11-28", "eligibility": "Met"}
        ]
    }

# 6. SKILLS MATRIX MODULE
@router.get("/skills/{student_id}")
def get_skills_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM skills WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Skills data not found")

    sk = dict(row)
    conn.close()

    return {
        "radar": [
            {"skill": "DSA & Algorithms", "score": sk["dsa_score"], "cohort_avg": 72.0},
            {"skill": "Full Stack Web", "score": sk["web_dev_score"], "cohort_avg": 70.5},
            {"skill": "AI & Machine Learning", "score": sk["ai_ml_score"], "cohort_avg": 68.0},
            {"skill": "Cloud & DevOps", "score": sk["cloud_score"], "cohort_avg": 65.0},
            {"skill": "Problem Solving", "score": sk["problem_solving_score"], "cohort_avg": 74.0},
            {"skill": "Soft Skills & Communication", "score": sk["soft_skills_score"], "cohort_avg": 76.0}
        ],
        "top_skill": sk["top_skill"],
        "recommended_upskill": sk["recommended_upskill"]
    }

# 7. FACULTY / LECTURE FEEDBACK MODULE
class FacultyFeedbackSubmission(BaseModel):
    student_id: str
    course_code: str
    course_name: str
    faculty_name: str
    rating: float
    pedagogy_rating: float
    clarity_rating: float
    pace_rating: float
    comment: str

@router.get("/faculty-feedback")
def get_faculty_feedback(course_code: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if course_code:
        cursor.execute("SELECT * FROM faculty_feedback WHERE course_code = ? ORDER BY created_at DESC", (course_code,))
    else:
        cursor.execute("SELECT * FROM faculty_feedback ORDER BY created_at DESC LIMIT 30")
    
    rows = [dict(r) for r in cursor.fetchall()]

    # Faculty summary aggregates
    cursor.execute("""
    SELECT faculty_name, course_name, AVG(rating) as avg_rating, COUNT(*) as feedback_count
    FROM faculty_feedback
    GROUP BY faculty_name, course_name
    """)
    summary = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "recent_feedback": rows,
        "faculty_summary": summary
    }

@router.post("/faculty-feedback")
def submit_faculty_feedback(fb: FacultyFeedbackSubmission):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO faculty_feedback (student_id, course_code, course_name, faculty_name, rating, pedagogy_rating, clarity_rating, pace_rating, comment)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fb.student_id, fb.course_code, fb.course_name, fb.faculty_name,
        fb.rating, fb.pedagogy_rating, fb.clarity_rating, fb.pace_rating, fb.comment
    ))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Thank you! Lecture feedback submitted successfully."}

# 8. RISK IDENTIFICATION MODULE
@router.get("/risk/{student_id}")
def get_risk_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_success WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Risk record not found")

    r_dict = dict(row)
    r_dict["top_risk_factors"] = json.loads(r_dict["top_risk_factors"]) if r_dict["top_risk_factors"] else []
    conn.close()

    return {
        "risk_assessment": r_dict,
        "early_warning_status": {
            "level": r_dict["risk_level"],
            "dropout_probability": r_dict["dropout_probability"],
            "intervention_recommended": r_dict["risk_level"] in ["High", "Medium"],
            "statutory_alert": "Critical: Multi-parameter shortfall detected" if r_dict["risk_level"] == "High" else "Normal Academic Standing"
        }
    }

# 9. STUDENT SUCCESS SCORE (SSS) MODULE
@router.get("/success-score/{student_id}")
def get_student_success_score_module(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        ss.*, 
        s.name, s.department,
        am.current_gpa, 
        att.attendance_rate,
        lms.assignment_submission_rate,
        sk.problem_solving_score,
        eng.wellbeing_score
    FROM student_success ss
    JOIN students s ON ss.student_id = s.id
    JOIN academic_metrics am ON ss.student_id = am.student_id
    JOIN attendance att ON ss.student_id = att.student_id
    JOIN lms_data lms ON ss.student_id = lms.student_id
    JOIN skills sk ON ss.student_id = sk.student_id
    JOIN engagement eng ON ss.student_id = eng.student_id
    WHERE ss.student_id = ?
    """, (student_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Success score not found")

    d = dict(row)
    conn.close()

    # Form components
    acad_score = round((d["current_gpa"] / 10.0) * 100, 1)
    att_score = round(d["attendance_rate"], 1)
    lms_score = round(d["assignment_submission_rate"], 1)
    skill_score = round(d["problem_solving_score"], 1)
    eng_score = round(d["wellbeing_score"] * 10.0, 1)

    return {
        "student_id": d["student_id"],
        "student_name": d["name"],
        "success_score": d["success_score"],
        "tier": d["tier"],
        "percentile": d["percentile"],
        "components": [
            {"dimension": "Academic Performance (35%)", "score": acad_score, "weighted": round(acad_score * 0.35, 1)},
            {"dimension": "Lecture & Lab Attendance (25%)", "score": att_score, "weighted": round(att_score * 0.25, 1)},
            {"dimension": "LMS Courseware Engagement (15%)", "score": lms_score, "weighted": round(lms_score * 0.15, 1)},
            {"dimension": "Technical Skills Matrix (15%)", "score": skill_score, "weighted": round(skill_score * 0.15, 1)},
            {"dimension": "Pulse & Holistic Engagement (10%)", "score": eng_score, "weighted": round(eng_score * 0.10, 1)}
        ],
        "recommendations": [
            f"Maintain attendance strictly above 80% to retain {d['tier']} status.",
            "Complete Unit 4 LMS Quiz before the upcoming internal assessment.",
            "Schedule peer coaching in Data Structures & Discrete Math."
        ]
    }
