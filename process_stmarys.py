import json
import random
import re
from app.data.raw_stmarys import RAW_CSV

CSE_COURSES = [
    {"code": "CS301", "name": "Data Structures & Algorithms", "credits": 4, "is_bottleneck": True},
    {"code": "CS302", "name": "Operating Systems", "credits": 4, "is_bottleneck": True},
    {"code": "CS303", "name": "Database Management Systems", "credits": 3, "is_bottleneck": False},
    {"code": "CS304", "name": "Computer Organization & Architecture", "credits": 3, "is_bottleneck": False},
    {"code": "MA301", "name": "Discrete Mathematics", "credits": 4, "is_bottleneck": True}
]

def clean_name(raw_name):
    name = raw_name.strip()
    name = re.sub(r'\s+', ' ', name)
    return " ".join([word.capitalize() for word in name.split(" ")])

def get_section(roll_no):
    code_suffix = roll_no[-4:].upper() if len(roll_no) >= 4 else "0501"
    # Section assignment based on JNTU / Telangana engineering batch division
    if code_suffix <= "0560":
        return "CSE - Section A"
    elif code_suffix <= "05C0":
        return "CSE - Section B"
    else:
        return "CSE - Section C"

def build_student_records():
    random.seed(101)
    lines = RAW_CSV.strip().split("\n")[1:]
    
    students = []
    
    for idx, line in enumerate(lines, 1):
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) < 2:
            continue
            
        raw_name = parts[0]
        username = parts[1]
        
        name = clean_name(raw_name)
        roll_no = username.split("@")[0].upper()
        email = username.lower()
        section = get_section(roll_no)
        
        # Give Rohith Yanamalla (the creator!) top academic standing
        is_user = "ROHITH YANAMALLA" in raw_name.upper() or "25D01A05F1" in roll_no
        
        if is_user:
            profile = "LOW_RISK"
            current_gpa = 9.4
            prior_gpa = 9.1
            attendance_rate = 94.5
            lab_attendance = 96.0
            assignment_rate = 98.0
            lms_logins = 18
            midterm_avg = 92.5
            fee_overdue = False
            first_gen = False
            wellbeing = 9
            risk_label = "Low"
            dropout_prob = 5.2
        else:
            r = random.random()
            if r < 0.18:
                profile = "HIGH_RISK"
                attendance_rate = round(random.uniform(52.0, 72.5), 1)
                lab_attendance = round(random.uniform(48.0, 71.0), 1)
                assignment_rate = round(random.uniform(45.0, 68.0), 1)
                lms_logins = random.randint(1, 4)
                midterm_avg = round(random.uniform(34.0, 56.0), 1)
                current_gpa = round(random.uniform(4.5, 6.2), 2)
                prior_gpa = round(min(10.0, current_gpa + random.uniform(0.7, 1.6)), 2)
                fee_overdue = random.random() < 0.35
                first_gen = random.random() < 0.40
                wellbeing = random.randint(2, 5)
                risk_label = "High"
                dropout_prob = round(random.uniform(68.0, 92.0), 1)
            elif r < 0.44:
                profile = "MEDIUM_RISK"
                attendance_rate = round(random.uniform(73.0, 79.5), 1)
                lab_attendance = round(random.uniform(71.0, 81.0), 1)
                assignment_rate = round(random.uniform(70.0, 82.0), 1)
                lms_logins = random.randint(5, 8)
                midterm_avg = round(random.uniform(58.0, 72.0), 1)
                current_gpa = round(random.uniform(6.4, 7.4), 2)
                prior_gpa = round(min(10.0, current_gpa + random.uniform(-0.2, 0.7)), 2)
                fee_overdue = random.random() < 0.15
                first_gen = random.random() < 0.30
                wellbeing = random.randint(5, 7)
                risk_label = "Medium"
                dropout_prob = round(random.uniform(34.0, 60.0), 1)
            else:
                profile = "LOW_RISK"
                attendance_rate = round(random.uniform(82.0, 97.5), 1)
                lab_attendance = round(random.uniform(84.0, 99.0), 1)
                assignment_rate = round(random.uniform(86.0, 100.0), 1)
                lms_logins = random.randint(9, 20)
                midterm_avg = round(random.uniform(74.0, 96.0), 1)
                current_gpa = round(random.uniform(7.6, 9.6), 2)
                prior_gpa = round(min(10.0, max(6.0, current_gpa + random.uniform(-0.4, 0.4))), 2)
                fee_overdue = False
                first_gen = random.random() < 0.20
                wellbeing = random.randint(7, 10)
                risk_label = "Low"
                dropout_prob = round(random.uniform(4.0, 22.0), 1)

        sem1_gpa = round(max(5.0, min(10.0, prior_gpa + random.uniform(-0.3, 0.3))), 2)
        sem2_gpa = prior_gpa
        sem3_gpa = current_gpa
        gpa_history = [
            {"semester": "Sem 1", "gpa": sem1_gpa},
            {"semester": "Sem 2", "gpa": sem2_gpa},
            {"semester": "Sem 3", "gpa": sem3_gpa}
        ]

        courses = []
        for c in CSE_COURSES:
            if profile == "HIGH_RISK":
                c_score = round(random.uniform(32.0, 58.0), 1)
                c_att = round(random.uniform(48.0, 72.0), 1)
            elif profile == "MEDIUM_RISK":
                c_score = round(random.uniform(58.0, 74.0), 1)
                c_att = round(random.uniform(72.0, 83.0), 1)
            else:
                c_score = round(random.uniform(76.0, 98.0), 1)
                c_att = round(random.uniform(84.0, 99.0), 1)

            courses.append({
                "code": c["code"],
                "name": c["name"],
                "credits": c["credits"],
                "is_bottleneck": c["is_bottleneck"],
                "current_score": c_score,
                "attendance": c_att,
                "assignments_done": f"{int(c_att/20)}/5"
            })

        top_risk_factors = []
        if attendance_rate < 75.0:
            top_risk_factors.append(f"Low overall attendance ({attendance_rate}%, statutory threshold 75%)")
        if (prior_gpa - current_gpa) >= 0.7:
            top_risk_factors.append(f"Steep GPA drop of {round(prior_gpa - current_gpa, 2)} pts since last semester")
        if assignment_rate < 70.0:
            top_risk_factors.append(f"High LMS non-compliance ({assignment_rate}% assignment submissions)")
        if lms_logins <= 4:
            top_risk_factors.append(f"Digital disengagement: Only {lms_logins} LMS logins/week")
        if midterm_avg < 50.0:
            top_risk_factors.append(f"Critical mid-term shortfall (Average score: {midterm_avg}%)")
        if wellbeing <= 4:
            top_risk_factors.append(f"Pulse survey wellbeing warning ({wellbeing}/10)")
        if fee_overdue:
            top_risk_factors.append("Administrative fee clearance overdue")

        if not top_risk_factors:
            top_risk_factors.append("Consistent academic progression across all parameters")

        students.append({
            "id": roll_no,
            "name": name,
            "email": email,
            "phone": f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
            "department": section,
            "branch": "Computer Science & Engineering",
            "institution": "St. Mary's Group of Institutions",
            "year": 2,
            "semester": 3,
            "avatar_color": random.choice(["#2563EB", "#059669", "#7C3AED", "#D97706", "#DB2777", "#0891B2"]),
            "metrics": {
                "attendance_rate": attendance_rate,
                "lab_attendance": lab_attendance,
                "assignment_submission_rate": assignment_rate,
                "lms_logins_weekly": lms_logins,
                "midterm_avg": midterm_avg,
                "current_gpa": current_gpa,
                "prior_gpa": prior_gpa,
                "gpa_delta": round(current_gpa - prior_gpa, 2),
                "fee_overdue": fee_overdue,
                "first_gen": first_gen,
                "wellbeing_score": wellbeing
            },
            "risk_assessment": {
                "level": risk_label,
                "dropout_probability": dropout_prob,
                "top_risk_factors": top_risk_factors[:3]
            },
            "gpa_trajectory": gpa_history,
            "courses": courses,
            "interventions": [
                {
                    "date": "2026-09-20",
                    "type": "Midterm Check-in",
                    "status": "In Progress",
                    "advisor": "Prof. K. Venkatesh"
                }
            ] if profile != "LOW_RISK" else []
        })

    return students

if __name__ == "__main__":
    records = build_student_records()
    out_file = "app/data/students_db.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"Successfully processed and saved {len(records)} students from St. Mary's Group to {out_file}!")
