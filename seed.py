import re
import json
import random
import os
import sys
from datetime import datetime

# Ensure project root is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_proj_root = os.path.dirname(os.path.dirname(_current_dir))
if _proj_root not in sys.path:
    sys.path.insert(0, _proj_root)

from app.db.database import get_connection, init_db
from app.data.raw_stmarys import RAW_CSV

COURSES = [
    {"code": "CS303", "name": "Database Management Systems (DBMS)", "short": "DBMS", "credits": 4, "faculty": "Prof. Sambhashiva"},
    {"code": "CS302", "name": "Java Programming", "short": "Java", "credits": 4, "faculty": "Prof. L.N. Rao"},
    {"code": "HS301", "name": "Industrial Economics (IE)", "short": "IE", "credits": 3, "faculty": "Prof. Ramudu"},
    {"code": "CS305", "name": "Software Engineering (SE)", "short": "SE", "credits": 3, "faculty": "Prof. Manohar"},
    {"code": "CS304", "name": "Computer Organization & Architecture (COA)", "short": "COA", "credits": 3, "faculty": "Prof. Sampath"},
    {"code": "CRT301", "name": "Campus Recruitment Training (CRT)", "short": "CRT", "credits": 2, "faculty": "Prof. Chakiri"},
    {"code": "MA301", "name": "Discrete Mathematics (DM)", "short": "DM", "credits": 4, "faculty": "Prof. Sateesh"}
]

def clean_name(raw_name):
    name = raw_name.strip()
    name = re.sub(r'\s+', ' ', name)
    return " ".join([word.capitalize() for word in name.split(" ")])

def get_section(roll_no):
    code_suffix = roll_no[-4:].upper() if len(roll_no) >= 4 else "0501"
    if code_suffix <= "0560":
        return "Section A"
    elif code_suffix <= "05C0":
        return "Section B"
    else:
        return "Section C"

def seed_database():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear previous seed
    cursor.execute("DELETE FROM fee_payments")
    cursor.execute("DELETE FROM recorrections")
    cursor.execute("DELETE FROM exam_results")
    cursor.execute("DELETE FROM faculty_feedback")
    cursor.execute("DELETE FROM student_success")
    cursor.execute("DELETE FROM skills")
    cursor.execute("DELETE FROM placements")
    cursor.execute("DELETE FROM engagement")
    cursor.execute("DELETE FROM lms_data")
    cursor.execute("DELETE FROM attendance")
    cursor.execute("DELETE FROM academic_metrics")
    cursor.execute("DELETE FROM students")
    cursor.execute("DELETE FROM users")

    # Add Default Institutional Advisor / Dean Account
    cursor.execute("""
    INSERT INTO users (id, username, password, display_name, license, role, email, roll_no)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "ADMIN_001",
        "admin@stmarysgroup.com",
        "admin123",
        "Dr. K. Venkatesh (Dean Academics)",
        "Enterprise Institutional Dean License",
        "advisor",
        "dean.academics@stmarysgroup.com",
        "FAC001"
    ))

    random.seed(42)
    lines = RAW_CSV.strip().split("\n")[1:]
    
    total_records = len(lines)
    student_records = []

    for idx, line in enumerate(lines, 1):
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) < 3:
            continue
            
        raw_name = parts[0]
        username = parts[1]
        password = parts[2]
        license_str = parts[3] if len(parts) > 3 else "Microsoft 365 A3 for students use benefit"
        
        name = clean_name(raw_name)
        roll_no = username.split("@")[0].upper()
        email = username.lower()
        section = get_section(roll_no)
        dept = f"CSE - {section}"
        
        # User profile identification (Rohith Yanamalla top star student profile)
        is_star = "ROHITH YANAMALLA" in raw_name.upper() or "25D01A05F1" in roll_no
        
        # Insert user account
        cursor.execute("""
        INSERT INTO users (id, username, password, display_name, license, role, email, roll_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no,
            username,
            password,
            name,
            license_str,
            "student",
            email,
            roll_no
        ))

        # Avatar color
        avatar_color = random.choice(["#2563EB", "#059669", "#7C3AED", "#D97706", "#DB2777", "#0891B2"])

        # Insert student record
        cursor.execute("""
        INSERT INTO students (id, roll_no, name, email, phone, department, branch, section, institution, year, semester, avatar_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no,
            roll_no,
            name,
            email,
            f"+91 9{random.randint(100000000, 999999999)}",
            dept,
            "Computer Science & Engineering",
            section,
            "St. Mary's Group of Institutions",
            2,
            3,
            avatar_color
        ))

        # Generate Metrics
        if is_star:
            current_gpa = 9.45
            prior_gpa = 9.20
            sem1_gpa = 9.10
            sem2_gpa = 9.20
            sem3_gpa = 9.45
            backlogs = 0
            att_rate = 96.5
            lab_att = 98.0
            theory_att = 95.0
            weekly_logins = 19
            assign_rate = 98.0
            quiz_score = 94.0
            hackathons = 4
            wellbeing = 9
            readiness = 94.0
            risk_tier = "Low"
            dropout_p = 3.5
        else:
            r = random.random()
            if r < 0.20: # High Risk
                current_gpa = round(random.uniform(4.5, 6.2), 2)
                prior_gpa = round(min(9.5, current_gpa + random.uniform(0.6, 1.5)), 2)
                sem1_gpa = round(prior_gpa + random.uniform(0.2, 0.5), 2)
                sem2_gpa = prior_gpa
                sem3_gpa = current_gpa
                backlogs = random.randint(1, 3)
                att_rate = round(random.uniform(55.0, 72.0), 1)
                lab_att = round(random.uniform(52.0, 71.0), 1)
                theory_att = round(random.uniform(56.0, 73.0), 1)
                weekly_logins = random.randint(1, 4)
                assign_rate = round(random.uniform(48.0, 68.0), 1)
                quiz_score = round(random.uniform(42.0, 60.0), 1)
                hackathons = random.randint(0, 1)
                wellbeing = random.randint(2, 5)
                readiness = round(random.uniform(40.0, 60.0), 1)
                risk_tier = "High"
                dropout_p = round(random.uniform(68.0, 92.0), 1)
            elif r < 0.50: # Medium Risk
                current_gpa = round(random.uniform(6.4, 7.5), 2)
                prior_gpa = round(current_gpa + random.uniform(-0.3, 0.6), 2)
                sem1_gpa = round(prior_gpa + random.uniform(-0.2, 0.4), 2)
                sem2_gpa = prior_gpa
                sem3_gpa = current_gpa
                backlogs = 0 if random.random() > 0.3 else 1
                att_rate = round(random.uniform(73.5, 81.0), 1)
                lab_att = round(random.uniform(74.0, 84.0), 1)
                theory_att = round(random.uniform(72.0, 80.0), 1)
                weekly_logins = random.randint(5, 8)
                assign_rate = round(random.uniform(72.0, 84.0), 1)
                quiz_score = round(random.uniform(68.0, 80.0), 1)
                hackathons = random.randint(1, 2)
                wellbeing = random.randint(5, 7)
                readiness = round(random.uniform(65.0, 78.0), 1)
                risk_tier = "Medium"
                dropout_p = round(random.uniform(32.0, 58.0), 1)
            else: # Low Risk
                current_gpa = round(random.uniform(7.8, 9.5), 2)
                prior_gpa = round(max(6.5, min(10.0, current_gpa + random.uniform(-0.4, 0.3))), 2)
                sem1_gpa = round(prior_gpa + random.uniform(-0.2, 0.3), 2)
                sem2_gpa = prior_gpa
                sem3_gpa = current_gpa
                backlogs = 0
                att_rate = round(random.uniform(84.0, 98.0), 1)
                lab_att = round(random.uniform(86.0, 99.0), 1)
                theory_att = round(random.uniform(83.0, 97.0), 1)
                weekly_logins = random.randint(9, 18)
                assign_rate = round(random.uniform(86.0, 100.0), 1)
                quiz_score = round(random.uniform(80.0, 96.0), 1)
                hackathons = random.randint(2, 5)
                wellbeing = random.randint(7, 10)
                readiness = round(random.uniform(80.0, 96.0), 1)
                risk_tier = "Low"
                dropout_p = round(random.uniform(4.0, 22.0), 1)

        gpa_delta = round(current_gpa - prior_gpa, 2)
        total_classes = 180
        attended_classes = int(total_classes * (att_rate / 100.0))
        condonation = 1 if att_rate < 75.0 else 0

        # Academic Metrics
        cursor.execute("""
        INSERT INTO academic_metrics (student_id, current_gpa, prior_gpa, gpa_delta, sem1_gpa, sem2_gpa, sem3_gpa, credits_completed, total_credits, backlogs, class_rank, total_students)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, current_gpa, prior_gpa, gpa_delta, sem1_gpa, sem2_gpa, sem3_gpa, 64, 160, backlogs, idx, total_records
        ))

        # Attendance
        cursor.execute("""
        INSERT INTO attendance (student_id, attendance_rate, lab_attendance, theory_attendance, total_classes, attended_classes, medical_leaves, condonation_required)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, att_rate, lab_att, theory_att, total_classes, attended_classes, random.randint(0, 4), condonation
        ))

        # LMS
        cursor.execute("""
        INSERT INTO lms_data (student_id, weekly_logins, assignment_submission_rate, modules_completed, total_modules, video_watch_hours, forum_posts, avg_quiz_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, weekly_logins, assign_rate, int(assign_rate / 10), 10, round(weekly_logins * 2.8, 1), random.randint(1, 15), quiz_score
        ))

        # Engagement
        sentiment = "Positive" if wellbeing >= 7 else ("Neutral" if wellbeing >= 5 else "Stressed/At-Risk")
        cursor.execute("""
        INSERT INTO engagement (student_id, participation_score, extracurricular_score, club_memberships, hackathons_attended, workshops_attended, wellbeing_score, sentiment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, round(att_rate * 0.9, 1), round(random.uniform(60, 95), 1), random.randint(1, 3), hackathons, random.randint(1, 4), wellbeing, sentiment
        ))

        # Placements
        el_status = "Eligible - Premium Tier" if current_gpa >= 7.5 and backlogs == 0 else ("Eligible - Core Tier" if current_gpa >= 6.0 and backlogs == 0 else "Criteria At-Risk")
        cursor.execute("""
        INSERT INTO placements (student_id, eligibility_status, readiness_score, mock_interview_score, coding_score, resume_ats_score, target_domain, dream_companies, offers_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, el_status, readiness, round(readiness * 0.95, 1), round(readiness * 0.92, 1), round(random.uniform(70, 96), 1),
            random.choice(["Full Stack Development", "Cloud & DevOps", "AI / Data Engineering", "Cybersecurity", "Embedded Systems"]),
            "Google, Microsoft, TCS, Infosys, KPMG", 1 if is_star or (readiness > 88 and random.random() > 0.4) else 0
        ))

        # Skills Matrix
        dsa = round(min(100.0, current_gpa * 10.2 + random.uniform(-5, 5)), 1)
        web = round(min(100.0, current_gpa * 10.0 + random.uniform(-6, 8)), 1)
        aiml = round(min(100.0, current_gpa * 9.8 + random.uniform(-8, 8)), 1)
        cloud = round(min(100.0, current_gpa * 9.5 + random.uniform(-7, 7)), 1)
        soft = round(min(100.0, wellbeing * 10.0 + random.uniform(-5, 5)), 1)
        problem = round(min(100.0, current_gpa * 10.3 + random.uniform(-4, 6)), 1)

        cursor.execute("""
        INSERT INTO skills (student_id, dsa_score, web_dev_score, ai_ml_score, cloud_score, soft_skills_score, problem_solving_score, top_skill, recommended_upskill)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, dsa, web, aiml, cloud, soft, problem,
            "Data Structures & Algorithms" if dsa >= web else "Full-Stack Web Development",
            "Distributed Systems & Cloud Architecture"
        ))

        # Semester Results (5 courses)
        for c in COURSES:
            base_score = round(current_gpa * 9.6 + random.uniform(-8, 8), 1)
            base_score = max(35.0, min(99.0, base_score))
            internal = round(base_score * 0.3, 1)
            external = round(base_score * 0.7, 1)
            tot = internal + external
            
            if tot >= 90:
                grd, pts = "O", 10.0
            elif tot >= 80:
                grd, pts = "A+", 9.0
            elif tot >= 70:
                grd, pts = "A", 8.0
            elif tot >= 60:
                grd, pts = "B+", 7.0
            elif tot >= 50:
                grd, pts = "B", 6.0
            elif tot >= 40:
                grd, pts = "C", 5.0
            else:
                grd, pts = "F", 0.0

            cursor.execute("""
            INSERT INTO exam_results (student_id, semester, course_code, course_name, credits, internal_marks, external_marks, total_marks, grade, grade_points, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no, "Sem 3", c["code"], c["name"], c["credits"], internal, external, tot, grd, pts, "PASS" if grd != "F" else "ARREAR"
            ))

        # Re-corrections (Seed a few realistic sample requests)
        if risk_tier == "High" or (idx % 8 == 0):
            target_c = COURSES[1] # OS or Discrete Math
            cursor.execute("""
            INSERT INTO recorrections (student_id, course_code, course_name, semester, original_marks, original_grade, revised_marks, revised_grade, request_type, reason, fee_amount, fee_paid, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no, target_c["code"], target_c["name"], "Sem 3", 44.0, "C", 56.0 if idx % 2 == 0 else None, "B" if idx % 2 == 0 else None,
                "Revaluation", "Discrepancy in Part B Q3 algorithm marks calculation", 500.0, 1,
                "Completed - Grade Revised" if idx % 2 == 0 else "Under Evaluation by Board"
            ))

        # Fee Payments (Exam, Bus, Hostel, Tuition)
        # 1. Exam Fee (₹2,500)
        exam_status = "Paid" if not (risk_tier == "High" and idx % 2 == 0) else "Pending"
        cursor.execute("""
        INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, transaction_id, payment_date, payment_method, invoice_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, "Exam Fee", "End Semester Examination Fee (Sem 3)", 2500.0, "2026-11-15", exam_status,
            f"TXN_EXAM_{roll_no}_{random.randint(1000, 9999)}" if exam_status == "Paid" else None,
            "2026-10-02" if exam_status == "Paid" else None,
            "UPI / PhonePe" if exam_status == "Paid" else None,
            f"INV-EXM-2026-{idx:04d}"
        ))

        # 2. College Bus Transportation Fee (₹28,000)
        bus_enrolled = (idx % 2 == 0)
        if bus_enrolled:
            bus_status = "Paid" if random.random() > 0.3 else "Pending"
            cursor.execute("""
            INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, transaction_id, payment_date, payment_method, invoice_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no, "Bus Fee", "Campus Route Transit Pass (Route 14)", 28000.0, "2026-10-30", bus_status,
                f"TXN_BUS_{roll_no}_{random.randint(1000, 9999)}" if bus_status == "Paid" else None,
                "2026-09-18" if bus_status == "Paid" else None,
                "HDFC NetBanking" if bus_status == "Paid" else None,
                f"INV-BUS-2026-{idx:04d}"
            ))

        # 3. Hostel & Mess Fee (₹45,000)
        hostel_enrolled = (idx % 3 == 0)
        if hostel_enrolled:
            hostel_status = "Paid" if random.random() > 0.25 else "Overdue"
            cursor.execute("""
            INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, transaction_id, payment_date, payment_method, invoice_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no, "Hostel Fee", "Campus Residence & Boarding (Block B, Room 204)", 45000.0, "2026-09-25", hostel_status,
                f"TXN_HST_{roll_no}_{random.randint(1000, 9999)}" if hostel_status == "Paid" else None,
                "2026-09-10" if hostel_status == "Paid" else None,
                "Credit Card" if hostel_status == "Paid" else None,
                f"INV-HST-2026-{idx:04d}"
            ))

        # 4. Tuition Fee (₹65,000)
        tuition_status = "Paid" if risk_tier != "High" or random.random() > 0.4 else "Overdue"
        cursor.execute("""
        INSERT INTO fee_payments (student_id, fee_type, title, amount, due_date, status, transaction_id, payment_date, payment_method, invoice_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, "Tuition Fee", "B.Tech Computer Science Academic Tuition", 65000.0, "2026-10-10", tuition_status,
            f"TXN_TUI_{roll_no}_{random.randint(1000, 9999)}" if tuition_status == "Paid" else None,
            "2026-08-25" if tuition_status == "Paid" else None,
            "SBI NEFT / RTGS" if tuition_status == "Paid" else None,
            f"INV-TUI-2026-{idx:04d}"
        ))

        # Faculty Feedback tailored specifically to each subject & professor
        FACULTY_COMMENTS = {
            "Prof. Sambhashiva": [
                "Prof. Sambhashiva explains SQL normalization, B+ Trees, and ACID transactions with intuitive schema examples.",
                "Excellent practical query optimization sessions in the database lab. Very approachable for doubts.",
                "Takes real-time enterprise scenarios to illustrate database design and relational constraints."
            ],
            "Prof. L.N. Rao": [
                "Prof. L.N. Rao makes Object-Oriented principles, multi-threading, and Collections framework crystal clear.",
                "Live coding sessions in Java are outstanding. Helps build deep intuition on JVM internals and Exception handling.",
                "Gives regular coding assignments in Java that directly prepare us for tech placement rounds."
            ],
            "Prof. Ramudu": [
                "Prof. Ramudu explains industrial economics, break-even analysis, and managerial decision models effectively.",
                "Connects economic theories with real corporate financial analysis and cost benefit evaluation.",
                "Good pacing on accounting ratios, depreciation formulas, and engineering project economics."
            ],
            "Prof. Manohar": [
                "Prof. Manohar guides Agile Scrum workflows, sprint planning, and Software Requirement Specifications (SRS) thoroughly.",
                "Software design patterns and UML class diagrams are taught with structured industry case studies.",
                "Valuable team-based software engineering project reviews that simulate actual IT company environments."
            ],
            "Prof. Sampath": [
                "Prof. Sampath demystifies computer architecture, instruction pipelining, and cache memory mapping with great diagrams.",
                "Explains CPU micro-architecture, memory hierarchy, and I/O organization with clarity.",
                "Systematic blackboard derivations on addressing modes and ALU data path design."
            ],
            "Prof. Chakiri": [
                "Prof. Chakiri provides high-impact quantitative aptitude shortcuts and campus recruitment training strategies.",
                "Logical reasoning and technical interview communication sessions give massive confidence for MNC drives.",
                "Excellent timed aptitude mock tests and company-specific CRT practice sessions."
            ],
            "Prof. Sateesh": [
                "Prof. Sateesh breaks down discrete mathematics, graph theory traversals, and combinatorics step-by-step.",
                "Makes mathematical induction, recurrence relations, and propositional logic engaging and easy to solve.",
                "Very patient in clarifying mathematical proof techniques and discrete relations."
            ]
        }

        # Seed feedback for 2 distinct courses per student to ensure broad coverage
        for target_course in random.sample(COURSES, 2):
            f_name = target_course["faculty"]
            f_rating = round(random.uniform(4.0, 5.0), 1) if is_star or current_gpa >= 7.5 else round(random.uniform(3.5, 4.8), 1)
            f_comments_pool = FACULTY_COMMENTS.get(f_name, ["Very dedicated faculty with strong subject mastery."])
            selected_comment = random.choice(f_comments_pool)

            cursor.execute("""
            INSERT INTO faculty_feedback (student_id, course_code, course_name, faculty_name, rating, pedagogy_rating, clarity_rating, pace_rating, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_no, target_course["code"], target_course["name"], f_name,
                f_rating, round(min(5.0, f_rating + random.uniform(-0.2, 0.2)), 1),
                round(min(5.0, f_rating + random.uniform(-0.2, 0.2)), 1),
                round(min(5.0, f_rating + random.uniform(-0.3, 0.3)), 1),
                selected_comment
            ))

        # Calculate Composite Student Success Score (SSS) [0 - 100]
        # Weighted formula: Academic 35%, Attendance 25%, LMS 15%, Skills 15%, Engagement 10%
        acad_comp = (current_gpa / 10.0) * 100.0
        att_comp = att_rate
        lms_comp = (assign_rate * 0.6 + (min(20, weekly_logins) / 20.0) * 40.0)
        skills_comp = ((dsa + web + aiml + problem) / 4.0)
        eng_comp = (wellbeing * 10.0)

        sss = round(acad_comp * 0.35 + att_comp * 0.25 + lms_comp * 0.15 + skills_comp * 0.15 + eng_comp * 0.10, 1)
        sss = max(10.0, min(99.5, sss))

        tier = "Elite Vanguard" if sss >= 88.0 else ("Competent Scholar" if sss >= 70.0 else "Intervention Priority")
        
        # Risk factors
        risk_drivers = []
        if att_rate < 75.0:
            risk_drivers.append(f"Lecture attendance below statutory mandate ({att_rate}%)")
        if gpa_delta < -0.5:
            risk_drivers.append(f"Academic velocity drop of {abs(gpa_delta)} GPA pts")
        if assign_rate < 70.0:
            risk_drivers.append(f"LMS assignment non-submission ({assign_rate}%)")
        if wellbeing <= 4:
            risk_drivers.append(f"Low psychological wellbeing pulse ({wellbeing}/10)")
        if not risk_drivers:
            risk_drivers.append("Steady learning velocity across all semesters")

        cursor.execute("""
        INSERT INTO student_success (student_id, success_score, percentile, tier, risk_level, dropout_probability, top_risk_factors, academic_weight, attendance_weight, lms_weight, skills_weight, engagement_weight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_no, sss, round(100.0 - (idx / total_records * 100.0), 1), tier, risk_tier, dropout_p,
            json.dumps(risk_drivers), 35.0, 25.0, 15.0, 15.0, 10.0
        ))

    conn.commit()
    conn.close()
    print(f"Successfully seeded SQLite database with {total_records} students and enterprise relational tables!")

if __name__ == "__main__":
    seed_database()
