import random
from core.supabase_client import supabase

# ============================================
# GRADE MAPPING
# ============================================
def get_grade(marks):
    if marks >= 90: return 'A+'
    elif marks >= 80: return 'A'
    elif marks >= 75: return 'A-'
    elif marks >= 70: return 'B+'
    elif marks >= 65: return 'B'
    elif marks >= 60: return 'B-'
    elif marks >= 55: return 'C+'
    elif marks >= 50: return 'C'
    elif marks >= 45: return 'D'
    else: return 'F'


# ============================================
# EXAMINATION ID MAPPING
# ============================================
EXAM_MAPPING = {
    1: 1,   # Sem 1 - Mid
    2: 5,   # Sem 2 - End
    3: 2,   # Sem 3 - Mid
    4: 6,   # Sem 4 - End
    5: 3,   # Sem 5 - Mid
    6: 7,   # Sem 6 - End
    7: 4,   # Sem 7 - Mid
    8: 8,   # Sem 8 - End
}

# ============================================
# SUBJECT ID MAPPING (Semester-wise)
# ============================================
SUBJECTS_BY_SEMESTER = {
    1: [1, 2, 3, 4, 5, 6],
    2: [7, 8, 9, 10, 11, 12],
    3: [13, 14, 15, 16, 17, 18],
    4: [19, 20, 21, 22, 23, 24],
    5: [25, 26, 27, 28, 29, 30],
    6: [31, 32, 33, 34, 35, 36],
    7: [37, 38, 39, 40, 41, 42],
    8: [43, 44, 45, 46, 47, 48],
}


# ============================================
# GET MARKS BASED ON STUDENT DOMAIN
# ============================================
def get_marks_for_domain(student_id, subject_id):
    if student_id <= 25:
        # Programming domain - high marks in programming subjects
        programming_subjects = [1, 2, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 26, 30, 35, 36, 43, 44, 46, 47, 48]
        if subject_id in programming_subjects:
            return random.randint(70, 95)
        else:
            return random.randint(40, 75)

    elif student_id <= 50:
        # Database domain
        database_subjects = [3, 14, 27, 34, 44]
        if subject_id in database_subjects:
            return random.randint(70, 95)
        else:
            return random.randint(40, 75)

    else:
        # AI/ML domain
        ai_ml_subjects = [29, 31, 37, 43, 45]
        if subject_id in ai_ml_subjects:
            return random.randint(70, 95)
        else:
            return random.randint(40, 75)


# ============================================
# INSERT MARKS FOR A STUDENT
# ============================================
def insert_marks_for_student(student_id):
    total_inserted = 0

    for semester in range(1, 7):
        subject_ids = SUBJECTS_BY_SEMESTER.get(semester, [])
        exam_id = EXAM_MAPPING.get(semester)

        if not subject_ids or not exam_id:
            continue

        for subject_id in subject_ids:
            marks_obtained = get_marks_for_domain(student_id, subject_id)
            grade = get_grade(marks_obtained)

            try:
                supabase.table('student_marks').insert({
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'examination_id': exam_id,
                    'marks_obtained': marks_obtained,
                    'grade': grade,
                    'faculty_id': 1,
                    'remarks': None
                }).execute()
                total_inserted += 1
            except Exception as e:
                print(f"Error for student {student_id}, subject {subject_id}: {e}")

    return total_inserted


# ============================================
# MAIN FUNCTION
# ============================================
def main():
    print("=" * 60)
    print("Inserting Marks for All Students (Sem 1 to 6)")
    print("=" * 60)

    # Check if marks already exist
    check_res = supabase.table('student_marks').select('student_id', count='exact').limit(1).execute()
    
    # Get count properly
    existing_count = 0
    if hasattr(check_res, 'count'):
        existing_count = check_res.count
    elif hasattr(check_res, 'data') and check_res.data:
        existing_count = len(check_res.data)

    if existing_count > 0:
        print("WARNING: Marks already exist in database!")
        response = input("Delete existing marks and re-insert? (y/n): ")
        if response.lower() == 'y':
            # Delete all marks
            supabase.table('student_marks').delete().neq('marks_id', 0).execute()
            print("Existing marks deleted.")
        else:
            print("Exiting without changes.")
            return

    total_students = 75
    total_marks = 0

    for student_id in range(1, total_students + 1):
        inserted = insert_marks_for_student(student_id)
        total_marks += inserted
        print(f"Student {student_id}: {inserted} marks inserted")

    print("=" * 60)
    print(f"Total Marks Inserted: {total_marks}")
    print(f"Students Processed: {total_students}")
    print("=" * 60)


# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    main()