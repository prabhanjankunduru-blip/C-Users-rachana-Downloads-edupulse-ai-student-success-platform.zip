import os
import json
from app.data.process_stmarys import build_student_records

def generate_student_dataset(num_students=None, seed=None):
    return build_student_records()

def save_default_dataset(filepath="app/data/students_db.json"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    dataset = build_student_records()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"St. Mary's Group dataset loaded with {len(dataset)} student records at {filepath}")
    return dataset

if __name__ == "__main__":
    save_default_dataset()
