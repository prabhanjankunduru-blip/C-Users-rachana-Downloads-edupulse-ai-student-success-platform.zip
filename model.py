import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import os

FEATURE_NAMES = [
    "attendance_rate",
    "lab_attendance",
    "assignment_submission_rate",
    "lms_logins_weekly",
    "midterm_avg",
    "current_gpa",
    "gpa_delta",
    "wellbeing_score",
    "fee_overdue",
    "first_gen"
]

FEATURE_LABELS = {
    "attendance_rate": "Lecture Attendance",
    "lab_attendance": "Laboratory Attendance",
    "assignment_submission_rate": "LMS Assignment Completion",
    "lms_logins_weekly": "Digital Engagement (LMS Logins)",
    "midterm_avg": "Midterm Examination Average",
    "current_gpa": "Cumulative GPA",
    "gpa_delta": "Semester GPA Trajectory Drop",
    "wellbeing_score": "Sentiment & Pulse Survey Score",
    "fee_overdue": "Administrative Fee Overdue",
    "first_gen": "First Generation Student Context"
}

class StudentRiskPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        self.is_trained = False
        self.feature_importances_ = {}

    def extract_features(self, student_dict):
        m = student_dict.get("metrics", student_dict)
        return [
            float(m.get("attendance_rate", 75.0)),
            float(m.get("lab_attendance", 75.0)),
            float(m.get("assignment_submission_rate", 80.0)),
            float(m.get("lms_logins_weekly", 8)),
            float(m.get("midterm_avg", 65.0)),
            float(m.get("current_gpa", 7.0)),
            float(m.get("gpa_delta", 0.0)),
            float(m.get("wellbeing_score", 7)),
            1.0 if m.get("fee_overdue", False) else 0.0,
            1.0 if m.get("first_gen", False) else 0.0
        ]

    def train_on_students(self, students_list):
        X = []
        y = []
        for s in students_list:
            X.append(self.extract_features(s))
            level = s.get("risk_assessment", {}).get("level", "Low")
            # Target: 0 = Low, 1 = Medium, 2 = High
            label_map = {"Low": 0, "Medium": 1, "High": 2}
            y.append(label_map.get(level, 0))

        X = np.array(X)
        y = np.array(y)

        self.model.fit(X, y)
        self.is_trained = True

        # Store global feature importances
        for name, imp in zip(FEATURE_NAMES, self.model.feature_importances_):
            self.feature_importances_[name] = round(float(imp) * 100, 2)
            
        print("Trained Student Risk ML Model successfully!")
        print(f"Top global risk drivers: {dict(sorted(self.feature_importances_.items(), key=lambda x: x[1], reverse=True)[:4])}")

    def predict(self, student_dict):
        features = self.extract_features(student_dict)
        X = np.array([features])
        
        if not self.is_trained:
            # Fallback heuristic if called before fit
            m = student_dict.get("metrics", student_dict)
            prob = max(5.0, min(95.0, 100.0 - float(m.get("attendance_rate", 75.0))))
            level = "High" if prob > 65 else ("Medium" if prob > 30 else "Low")
            return {
                "level": level,
                "dropout_probability": round(prob, 1),
                "top_drivers": ["Attendance rate below threshold", "Low LMS engagement"]
            }

        probs = self.model.predict_proba(X)[0] # [P(Low), P(Med), P(High)]
        high_risk_prob = round(float(probs[2] * 100), 1) if len(probs) > 2 else 10.0
        med_risk_prob = round(float(probs[1] * 100), 1) if len(probs) > 1 else 20.0
        
        # Calculate composite dropout risk score
        composite_risk = round(high_risk_prob * 0.75 + med_risk_prob * 0.25, 1)

        if composite_risk >= 55.0:
            level = "High"
        elif composite_risk >= 25.0:
            level = "Medium"
        else:
            level = "Low"

        # Local Explainable AI (XAI) attribution: check negative deviance from ideal
        m = student_dict.get("metrics", student_dict)
        risk_drivers = []
        if float(m.get("attendance_rate", 100)) < 75.0:
            risk_drivers.append(f"Low overall attendance ({m.get('attendance_rate')}%, statutory limit 75%)")
        if float(m.get("gpa_delta", 0)) <= -0.6:
            risk_drivers.append(f"Steep academic decline (GPA dropped by {abs(float(m.get('gpa_delta')))} pts)")
        if float(m.get("assignment_submission_rate", 100)) < 70.0:
            risk_drivers.append(f"LMS assignment backlog ({m.get('assignment_submission_rate')}% submitted)")
        if float(m.get("midterm_avg", 100)) < 50.0:
            risk_drivers.append(f"Midterm exam critical failure risk (Avg: {m.get('midterm_avg')}%)")
        if float(m.get("lms_logins_weekly", 10)) <= 4:
            risk_drivers.append(f"Low LMS login frequency ({m.get('lms_logins_weekly')} visits/week)")
        if float(m.get("wellbeing_score", 10)) <= 4:
            risk_drivers.append(f"Pulse survey wellbeing warning ({m.get('wellbeing_score')}/10)")
        if m.get("fee_overdue", False):
            risk_drivers.append("Administrative fee payment overdue")

        if not risk_drivers:
            risk_drivers = ["Healthy attendance and consistent academic progression"]

        return {
            "level": level,
            "dropout_probability": max(4.0, min(95.0, composite_risk)),
            "probabilities": {
                "low": round(float(probs[0] * 100), 1),
                "medium": round(float(probs[1] * 100), 1) if len(probs) > 1 else 0.0,
                "high": round(float(probs[2] * 100), 1) if len(probs) > 2 else 0.0
            },
            "top_drivers": risk_drivers[:3]
        }

# Global predictor instance
predictor = StudentRiskPredictor()
