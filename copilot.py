from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import re
from app.db.database import get_connection

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

class CopilotChatRequest(BaseModel):
    query: str
    student_id: Optional[str] = None
    role: Optional[str] = "student"

@router.post("/chat")
def chat_with_copilot(req: CopilotChatRequest):
    q = req.query.strip().lower()
    sid = req.student_id

    conn = get_connection()
    cursor = conn.cursor()

    student_data = None
    if sid:
        cursor.execute("""
        SELECT s.*, am.current_gpa, am.gpa_delta, am.class_rank,
               att.attendance_rate, att.lab_attendance,
               lms.assignment_submission_rate, lms.weekly_logins,
               ss.success_score, ss.tier, ss.risk_level, ss.dropout_probability,
               plc.eligibility_status, plc.readiness_score, plc.target_domain
        FROM students s
        LEFT JOIN academic_metrics am ON s.id = am.student_id
        LEFT JOIN attendance att ON s.id = att.student_id
        LEFT JOIN lms_data lms ON s.id = lms.student_id
        LEFT JOIN student_success ss ON s.id = ss.student_id
        LEFT JOIN placements plc ON s.id = plc.student_id
        WHERE s.id = ? OR s.roll_no = ?
        """, (sid, sid))
        row = cursor.fetchone()
        if row:
            student_data = dict(row)

    # 1. At-Risk / Early Warning Query
    if "risk" in q or "dropout" in q or "at-risk" in q or "warning" in q:
        cursor.execute("""
        SELECT s.name, s.roll_no, am.current_gpa, att.attendance_rate, ss.risk_level, ss.dropout_probability
        FROM students s
        JOIN academic_metrics am ON s.id = am.student_id
        JOIN attendance att ON s.id = att.student_id
        JOIN student_success ss ON s.id = ss.student_id
        WHERE ss.risk_level = 'High'
        ORDER BY ss.dropout_probability DESC
        LIMIT 5
        """)
        high_risk_list = [dict(r) for r in cursor.fetchall()]
        conn.close()

        names_str = "\n".join([f"• **{s['name']}** ({s['roll_no']}): GPA {s['current_gpa']}, Attendance {s['attendance_rate']}%, Risk Probability: {s['dropout_probability']}%" for s in high_risk_list])
        
        reply = f"""### 🚨 AI Early Warning Diagnostic Summary
Institutional predictive models identify **{len(high_risk_list)} primary students** requiring immediate multi-parameter academic intervention:

{names_str}

**Prescriptive Actions:**
1. **Attendance Restorative Plan:** Initiate mandated contact for students under the 75% statutory boundary.
2. **Peer Mentoring:** Assign student tutors for CS301 (Data Structures) and MA301 (Discrete Math).
3. **Counseling Pulse:** Schedule 1-on-1 advisor sessions with the Dean's guidance team."""
        return {"reply": reply, "topic": "risk_management"}

    # 2. Fee / Payment Query
    if "fee" in q or "dues" in q or "payment" in q or "hostel" in q or "bus" in q or "exam fee" in q:
        if sid:
            cursor.execute("SELECT * FROM fee_payments WHERE student_id = ? AND status IN ('Pending', 'Overdue')", (sid,))
            pending_fees = [dict(r) for r in cursor.fetchall()]
            conn.close()
            if pending_fees:
                fee_lines = "\n".join([f"• **{f['title']}**: ₹{f['amount']:,.2f} *(Due: {f['due_date']}, Status: <span style='color:#e11d48;'>{f['status']}</span>)*" for f in pending_fees])
                total = sum(f["amount"] for f in pending_fees)
                reply = f"""### 💳 Institutional Fee Accounts Status
You currently have **{len(pending_fees)} outstanding fee payment(s)** totaling **₹{total:,.2f}**:

{fee_lines}

👉 You can immediately clear your dues using our integrated **Fee Payments Portal** tab with Instant Receipt generation (supports UPI, NetBanking, and Debit/Credit Cards)."""
            else:
                reply = "### ✅ Fee Accounts Cleared\nAll your semester fees (Tuition, Exam, Transport, and Hostel) have been fully paid. You have zero outstanding dues!"
        else:
            cursor.execute("SELECT fee_type, COUNT(*) as cnt, SUM(amount) as total FROM fee_payments WHERE status != 'Paid' GROUP BY fee_type")
            fee_summary = [dict(r) for r in cursor.fetchall()]
            conn.close()
            sum_lines = "\n".join([f"• **{f['fee_type']}**: ₹{f['total']:,.2f} pending across {f['cnt']} student invoices" for f in fee_summary])
            reply = f"### 📊 Institutional Fee Dues Overview\nInstitutional accounts summary for Fall 2026:\n\n{sum_lines}\n\nStudents can pay directly via the Fee Portal."
        return {"reply": reply, "topic": "fee_management"}

    # 3. Re-correction / Revaluation Query
    if "recorrection" in q or "re-correction" in q or "revaluation" in q or "marksheet" in q or "grade card" in q:
        conn.close()
        reply = """### 🔄 Semester Exam Re-correction Window (Active)
The official **St. Mary's Examination Board Revaluation Window** is currently open until **November 25, 2026**:

1. **Eligible Subjects:** CS301 (Data Structures), CS302 (Operating Systems), CS303 (DBMS), CS304 (COA), MA301 (Discrete Mathematics).
2. **Statutory Fee:** ₹500 per theory paper.
3. **Processing Steps:** 
   - Navigate to the **Re-corrections Window** button on the dashboard.
   - Select your target subject and state your justification.
   - Confirmation is recorded immediately in the Examination Controller ledger with live status tracking."""
        return {"reply": reply, "topic": "recorrections"}

    # 4. Student Success Score (SSS) Query
    if "success score" in q or "sss" in q or "score" in q or "percentile" in q:
        conn.close()
        if student_data:
            reply = f"""### 🌟 Student Success Score (SSS) Breakdown for {student_data['name']}
Your current AI composite score is **{student_data['success_score']} / 100** (Tier: **{student_data['tier']}**).

**Weighted Formula Breakdown:**
• **Academic Performance (35%):** Current GPA of {student_data['current_gpa']}/10.0
• **Attendance Compliance (25%):** {student_data['attendance_rate']}% lecture presence
• **LMS Courseware Engagement (15%):** {student_data['assignment_submission_rate']}% assignment submissions
• **Technical Skills Matrix (15%):** Evaluated across 6 engineering competencies
• **Holistic Engagement (10%):** Pulse survey and campus participation

🎯 *Recommendation:* Keeping your attendance above 85% and submitting all LMS modules will elevate your score into the top percentile!"""
        else:
            reply = """### 🌟 Student Success Score (SSS) Architecture
The EduPulse Student Success Score is a KPMG-standard 0-100 composite index calculated as:
$$\\text{SSS} = (\\text{Academic} \\times 0.35) + (\\text{Attendance} \\times 0.25) + (\\text{LMS} \\times 0.15) + (\\text{Skills} \\times 0.15) + (\\text{Engagement} \\times 0.10)$$

Students scoring $\\ge 88$ earn **Elite Vanguard**, $70 - 87$ earn **Competent Scholar**, and $< 70$ trigger **Intervention Priority**."""
        return {"reply": reply, "topic": "success_score"}

    # 5. Placements & Career Readiness
    if "placement" in q or "career" in q or "package" in q or "job" in q or "interview" in q:
        conn.close()
        if student_data:
            reply = f"""### 💼 Placement & Career Readiness Dossier for {student_data['name']}
• **Eligibility Tier:** {student_data['eligibility_status']}
• **Campus Readiness Index:** {student_data['readiness_score']} / 100
• **Specialized Target Track:** {student_data['target_domain']}

**Top Recruiter Drives Visiting St. Mary's Campus:**
1. **KPMG India** — Associate Technology Consultant (₹9.5 LPA) · Nov 20, 2026
2. **Google Cloud** — Solutions Associate (₹14.0 LPA) · Dec 05, 2026
3. **TCS Digital** — Systems Engineer (₹7.5 LPA) · Nov 28, 2026

*Action Item:* Practice LeetCode Tree/Graph traversals and optimize your ATS resume template in the Placements tab."""
        else:
            reply = """### 💼 Campus Placement Ecosystem
St. Mary's 2026 Placement Drive features tier-1 recruiting partners including **KPMG in India, Google Cloud, Microsoft, and TCS**.
Eligibility requires a minimum CGPA of 6.5 with 0 active backlogs. View individual scorecards in the Placements tab."""
        return {"reply": reply, "topic": "placements"}

    # 6. Faculty / Lecture Feedback Query
    if "faculty" in q or "feedback" in q or "lecturer" in q or "professor" in q or "sambhashiva" in q or "rao" in q or "ramudu" in q or "manohar" in q or "sampath" in q or "chakiri" in q or "sateesh" in q:
        cursor.execute("""
        SELECT faculty_name, course_name, AVG(rating) as avg_rating, COUNT(*) as eval_count
        FROM faculty_feedback
        GROUP BY faculty_name, course_name
        ORDER BY avg_rating DESC
        """)
        fac_stats = [dict(r) for r in cursor.fetchall()]
        conn.close()

        lines = "\n".join([f"• **{f['faculty_name']}** (*{f['course_name']}*): **{round(f['avg_rating'], 1)} / 5.0** ({f['eval_count']} student ratings)" for f in fac_stats])

        reply = f"""### 📝 Faculty & Lecture Feedback Summary
Department of Computer Science & Engineering faculty evaluation ratings:

{lines}

**Assigned Department Faculty Roster:**
1. **DBMS (Database Management Systems):** Prof. Sambhashiva
2. **Java (Java Programming):** Prof. L.N. Rao
3. **IE (Industrial Economics):** Prof. Ramudu
4. **SE (Software Engineering):** Prof. Manohar
5. **COA (Computer Organization & Architecture):** Prof. Sampath
6. **CRT (Campus Recruitment Training):** Prof. Chakiri
7. **DM (Discrete Mathematics):** Prof. Sateesh

👉 Students can submit anonymous lecture evaluations using the **Feedback of Lectures** tab."""
        return {"reply": reply, "topic": "faculty_feedback"}

    # 6. Default Contextual AI Response
    conn.close()
    student_ctx = f" Currently analyzing profile for student **{student_data['name']}** (Roll: {student_data['roll_no']}, GPA: {student_data['current_gpa']})." if student_data else ""
    
    reply = f"""### 🤖 KPMG EduPulse Institutional Copilot
I am your AI Success Copilot.{student_ctx}

Here are some high-impact queries I can assist you with right now:
1. **"Identify students with high dropout risk"** — Run predictive early warning analysis.
2. **"What is my Student Success Score (SSS)?"** — Explain composite metric breakdown.
3. **"Check my pending fee dues"** — List exam, tuition, transport, or hostel fees.
4. **"How do I submit a re-correction request?"** — Guide through revaluation window.
5. **"Check placement drive eligibility"** — Review mock interview & hiring stats.
6. **"Give faculty feedback report"** — View lecture evaluation ratings.

What specific student analytics or institutional intelligence would you like to explore?"""

    return {"reply": reply, "topic": "general_guidance"}
