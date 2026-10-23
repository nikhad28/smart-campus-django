from core.supabase_client import supabase

# Domain mapping based on subject codes
DOMAIN_MAPPING = {
    "Programming": [
        "CE106", "CE203", "CE205", "CE303", "CE306", 
        "CE401", "CE403", "CE404", "CE502", "CE605"
    ],
    "Database": [
        "CE302", "CE503", "CE604", "CE802"
    ],
    "Networking": [
        "CE402", "CE504", "CE703"
    ],
    "Operating_Systems": [
        "CE304", "CE305", "CE405", "CE602"
    ],
    "AI_ML": [
        "CE505", "CE601", "CE701", "CE801", "CE803"
    ],
    "Cybersecurity": [
        "CE603", "CE702", "CE704"
    ],
    "Mathematics": [
        "CE101", "CE201", "CE301", "CE406", "CE501"
    ],
    "Core_Engineering": [
        "CE102", "CE103", "CE104", "CE105", "CE202", "CE204", "CE705", "CE804"
    ],
    "Project_Internship": [
        "CE506", "CE606", "CE706", "CE805", "CE806"
    ]
}

class SkillPredictor:
    def __init__(self):
        self.domains = list(DOMAIN_MAPPING.keys())
    
    def get_student_subjects(self, student_id):
        """Get all subjects and marks for a student"""
        try:
            # ✅ CORRECT: Table name is 'student_marks' and 'subject'
            response = supabase.table('student_marks')\
                .select('*, subject:subject_id(*)')\
                .eq('student_id', student_id)\
                .execute()
            return response.data if hasattr(response, 'data') else []
        except Exception as e:
            print(f"Error fetching marks: {e}")
            return []
    
    def calculate_domain_scores(self, student_id):
        """Calculate domain-wise scores"""
        marks_data = self.get_student_subjects(student_id)
        
        if not marks_data:
            return {}
        
        domain_scores = {}
        domain_marks_count = {}
        
        for mark in marks_data:
            subject = mark.get('subject', {})
            subject_code = subject.get('subject_code', '')
            marks = mark.get('marks_obtained', 0)
            
            # Find which domain this subject belongs to
            for domain, codes in DOMAIN_MAPPING.items():
                if subject_code in codes:
                    if domain not in domain_scores:
                        domain_scores[domain] = 0
                        domain_marks_count[domain] = 0
                    domain_scores[domain] += marks
                    domain_marks_count[domain] += 1
                    break
        
        # Calculate averages
        for domain in domain_scores:
            if domain_marks_count.get(domain, 0) > 0:
                domain_scores[domain] = round(domain_scores[domain] / domain_marks_count[domain], 2)
        
        return domain_scores
    
    def predict(self, student_id):
        """Predict primary domain for a student"""
        scores = self.calculate_domain_scores(student_id)
        
        if not scores:
            return {
                'primary_domain': None,
                'domain_scores': {},
                'confidence': 0,
                'strengths': [],
                'weaknesses': []
            }
        
        # Find primary domain
        primary_domain = max(scores, key=scores.get)
        
        # Calculate confidence
        max_score = max(scores.values())
        min_score = min(scores.values()) if len(scores) > 1 else 0
        confidence = round(((max_score - min_score) / 100) * 100, 2) if max_score > min_score else 50
        
        # Get strengths and weaknesses
        marks_data = self.get_student_subjects(student_id)
        strengths = []
        weaknesses = []
        
        for mark in marks_data:
            subject = mark.get('subject', {})
            marks = mark.get('marks_obtained', 0)
            subject_name = subject.get('subject_name', '')
            
            if marks >= 75:
                strengths.append(subject_name)
            elif marks < 40:
                weaknesses.append(subject_name)
        
        return {
            'primary_domain': primary_domain,
            'domain_scores': scores,
            'confidence': confidence,
            'strengths': strengths[:5],
            'weaknesses': weaknesses[:5]
        }