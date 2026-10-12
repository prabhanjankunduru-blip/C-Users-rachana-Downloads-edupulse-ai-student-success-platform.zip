from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from datetime import datetime
from app.db.database import get_connection

router = APIRouter(prefix="/api/results", tags=["results"])

class RecorrectionRequest(BaseModel):
    student_id: str
    course_code: str
    course_name: str
    semester: str
    original_marks: float
    original_grade: str
    request_type: Optional[str] = "Revaluation" # Revaluation, Re-totalling, Script Copy
    reason: str
    fee_amount: Optional[float] = 500.0

@router.get("/{student_id}")
def get_student_results(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT er.*, s.name as student_name, s.roll_no, s.department
    FROM exam_results er
    JOIN students s ON er.student_id = s.id
    WHERE er.student_id = ?
    ORDER BY er.course_code ASC
    """, (student_id,))

    rows = [dict(r) for r in cursor.fetchall()]

    if not rows:
        conn.close()
        raise HTTPException(status_code=404, detail="No exam results found for this student")

    total_credits = sum(r["credits"] for r in rows)
    total_points = sum(r["credits"] * r["grade_points"] for r in rows)
    sgpa = round(total_points / max(1, total_credits), 2)
    has_arrears = any(r["status"] == "ARREAR" for r in rows)

    conn.close()

    return {
        "student_id": student_id,
        "semester": "Semester 3 (Fall 2026)",
        "sgpa": sgpa,
        "total_credits": total_credits,
        "result_status": "PROMOTED WITH DISTINCTION" if sgpa >= 8.5 else ("PROMOTED" if not has_arrears else "CONTAINS BACKLOGS"),
        "courses": rows
    }

@router.get("/recorrections/{student_id}")
def get_student_recorrections(student_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT rc.*, s.name as student_name, s.roll_no
    FROM recorrections rc
    JOIN students s ON rc.student_id = s.id
    WHERE rc.student_id = ?
    ORDER BY rc.requested_at DESC
    """, (student_id,))

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "student_id": student_id,
        "applications": rows,
        "revaluation_window_active": True,
        "window_deadline": "2026-11-25 23:59 IST",
        "fee_per_paper": 500.0
    }

@router.post("/recorrections")
def submit_recorrection(req: RecorrectionRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO recorrections (
        student_id, course_code, course_name, semester,
        original_marks, original_grade, request_type, reason,
        fee_amount, fee_paid, status, requested_at, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'Under Evaluation by Board', datetime('now'), datetime('now'))
    """, (
        req.student_id, req.course_code, req.course_name, req.semester,
        req.original_marks, req.original_grade, req.request_type, req.reason,
        req.fee_amount
    ))

    conn.commit()
    new_id = cursor.lastrowid

    cursor.execute("SELECT * FROM recorrections WHERE id = ?", (new_id,))
    record = dict(cursor.fetchone())
    conn.close()

    return {
        "success": True,
        "message": f"Re-correction application submitted successfully for {req.course_code} - {req.course_name}!",
        "application_id": f"RC-2026-{new_id:04d}",
        "details": record
    }
