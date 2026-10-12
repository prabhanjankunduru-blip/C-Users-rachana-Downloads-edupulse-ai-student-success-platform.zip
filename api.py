from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from app.ml.model import predictor
from app.services.gemini_service import generate_student_intervention, process_copilot_query
from app.data.generator import save_default_dataset, generate_student_dataset

router = APIRouter(prefix="/api", tags=["analytics"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "students_db.json")
STUDENTS_CACHE = []

def get_students():
    global STUDENTS_CACHE
    if not STUDENTS_CACHE:
        if os.path.exists(DB_PATH):
            with open(DB_PATH, "r", encoding="utf-8") as f:
                STUDENTS_CACHE = json.load(f)
        else:
            STUDENTS_CACHE = save_default_dataset(DB_PATH)
        
        # Ensure model is trained on this data
        if not predictor.is_trained and STUDENTS_CACHE:
            predictor.train_on_students(STUDENTS_CACHE)
            
    return STUDENTS_CACHE

@router.get("/overview")
def get_overview_metrics():
    students = get_students()
    total = len(students)
    if total == 0:
        raise HTTPException(status_code=500, detail="Database is empty")

    high_risk = sum(1 for s in students if s["risk_assessment"]["level"] == "High")
    med_risk = sum(1 for s in students if s["risk_assessment"]["level"] == "Medium")
    low_risk = sum(1 for s in students if s["risk_assessment"]["level"] == "Low")

    avg_attendance = round(sum(s["metrics"]["attendance_rate"] for s in students) / total, 1)
    avg_gpa = round(sum(s["metrics"]["current_gpa"] for s in students) / total, 2)
    avg_assignment = round(sum(s["metrics"]["assignment_submission_rate"] for s in students) / total, 1)

    # Department breakdown
    dept_map = {}
    for s in students:
        d = s["department"]
        if d not in dept_map:
            dept_map[d] = {"name": d, "total": 0, "high_risk": 0, "med_risk": 0, "low_risk": 0, "gpa_sum": 0, "att_sum": 0}
        dept_map[d]["total"] += 1
        lvl = s["risk_assessment"]["level"]
        if lvl == "High":
            dept_map[d]["high_risk"] += 1
        elif lvl == "Medium":
            dept_map[d]["med_risk"] += 1
        else:
            dept_map[d]["low_risk"] += 1
        dept_map[d]["gpa_sum"] += s["metrics"]["current_gpa"]
        dept_map[d]["att_sum"] += s["metrics"]["attendance_rate"]

    dept_stats = []
    for d, v in dept_map.items():
        cnt = v["total"]
        dept_stats.append({
            "department": d,
            "total_students": cnt,
            "high_risk_count": v["high_risk"],
            "high_risk_percentage": round((v["high_risk"] / cnt) * 100, 1),
            "avg_gpa": round(v["gpa_sum"] / cnt, 2),
            "avg_attendance": round(v["att_sum"] / cnt, 1)
        })

    # Bottleneck courses
    course_map = {}
    for s in students:
        for c in s.get("courses", []):
            code = c["code"]
            if code not in course_map:
                course_map[code] = {
                    "code": code,
                    "name": c["name"],
                    "is_bottleneck": c.get("is_bottleneck", False),
                    "total_enrolled": 0,
                    "struggling_count": 0,
                    "score_sum": 0
                }
            course_map[code]["total_enrolled"] += 1
            course_map[code]["score_sum"] += c["current_score"]
            if c["current_score"] < 60 or c["attendance"] < 70:
                course_map[code]["struggling_count"] += 1

    bottlenecks = []
    for code, c in course_map.items():
        if c["is_bottleneck"]:
            cnt = c["total_enrolled"]
            bottlenecks.append({
                "code": code,
                "name": c["name"],
                "struggle_rate": round((c["struggling_count"] / max(cnt, 1)) * 100, 1),
                "avg_score": round(c["score_sum"] / max(cnt, 1), 1),
                "total_students": cnt
            })

    bottlenecks.sort(key=lambda x: x["struggle_rate"], reverse=True)

    return {
        "kpis": {
            "total_students": total,
            "high_risk_count": high_risk,
            "high_risk_pct": round((high_risk / total) * 100, 1),
            "medium_risk_count": med_risk,
            "low_risk_count": low_risk,
            "avg_attendance": avg_attendance,
            "avg_gpa": avg_gpa,
            "avg_assignment_rate": avg_assignment,
            "critical_interventions_pending": high_risk
        },
        "department_analytics": dept_stats,
        "bottleneck_courses": bottlenecks[:5],
        "feature_importance": predictor.feature_importances_
    }

@router.get("/students")
def list_students(
    search: Optional[str] = None,
    risk: Optional[str] = "All",
    department: Optional[str] = "All",
    year: Optional[int] = None,
    low_attendance: Optional[bool] = False
):
    students = get_students()
    res = students

    if search:
        s_lower = search.lower()
        res = [s for s in res if s_lower in s["name"].lower() or s_lower in s["id"].lower() or s_lower in s["email"].lower()]

    if risk and risk != "All":
        res = [s for s in res if s["risk_assessment"]["level"] == risk]

    if department and department != "All":
        res = [s for s in res if s["department"] == department]

    if year and year > 0:
        res = [s for s in res if s["year"] == year]

    if low_attendance:
        res = [s for s in res if s["metrics"]["attendance_rate"] < 75.0]

    return {
        "total_matched": len(res),
        "students": res
    }

@router.get("/students/{student_id}")
def get_student_detail(student_id: str):
    students = get_students()
    for s in students:
        if s["id"] == student_id:
            # Re-run ML dynamic inference for the latest risk score & attribution
            prediction = predictor.predict(s)
            s_copy = dict(s)
            s_copy["risk_assessment"]["dropout_probability"] = prediction["dropout_probability"]
            s_copy["risk_assessment"]["level"] = prediction["level"]
            s_copy["risk_assessment"]["top_risk_factors"] = prediction["top_drivers"]
            s_copy["risk_assessment"]["probabilities"] = prediction.get("probabilities", {})
            return s_copy

    raise HTTPException(status_code=404, detail="Student not found")

@router.post("/students/{student_id}/intervention")
def request_student_intervention(student_id: str):
    students = get_students()
    target_student = None
    for s in students:
        if s["id"] == student_id:
            target_student = s
            break
            
    if not target_student:
        raise HTTPException(status_code=404, detail="Student not found")

    intervention = generate_student_intervention(target_student)
    return {
        "student_id": student_id,
        "student_name": target_student["name"],
        "intervention": intervention
    }

class CopilotQueryRequest(BaseModel):
    query: str

@router.post("/copilot/chat")
def copilot_chat(req: CopilotQueryRequest):
    students = get_students()
    result = process_copilot_query(req.query, students)
    return result

class WhatIfSimulationRequest(BaseModel):
    student_id: Optional[str] = None
    attendance_rate: float
    lab_attendance: float
    assignment_submission_rate: float
    lms_logins_weekly: int
    midterm_avg: float
    current_gpa: float
    gpa_delta: float
    wellbeing_score: int
    fee_overdue: bool
    first_gen: bool

@router.post("/simulate")
def simulate_risk(req: WhatIfSimulationRequest):
    """
    Interactive 'What-If' Simulation: Allows advisors to model how intervention
    outcomes (e.g. +15% attendance) change risk probability in real-time.
    """
    mock_dict = {
        "metrics": {
            "attendance_rate": req.attendance_rate,
            "lab_attendance": req.lab_attendance,
            "assignment_submission_rate": req.assignment_submission_rate,
            "lms_logins_weekly": req.lms_logins_weekly,
            "midterm_avg": req.midterm_avg,
            "current_gpa": req.current_gpa,
            "gpa_delta": req.gpa_delta,
            "wellbeing_score": req.wellbeing_score,
            "fee_overdue": req.fee_overdue,
            "first_gen": req.first_gen
        }
    }
    result = predictor.predict(mock_dict)
    return result
