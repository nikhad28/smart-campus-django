# core/utils/career_recommender.py
import pandas as pd
import numpy as np
import joblib
import os
from supabase import create_client
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import warnings
import json
from datetime import datetime

warnings.filterwarnings('ignore')

load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# DOMAIN MAPPING
# ============================================
DOMAINS = [
    'Programming / Software Development',
    'Database',
    'Networking',
    'AI / Machine Learning',
    'Data Science / Data Analytics',
    'Cybersecurity',
    'Cloud Computing'
]

# core/utils/career_recommender.py - Update CAREER_DOMAIN_MAPPING

CAREER_DOMAIN_MAPPING = {
    # Programming & Development
    'Software Developer': ['Programming / Software Development', 'Database'],
    'Full Stack Developer': ['Programming / Software Development', 'Database'],
    'Frontend Developer': ['Programming / Software Development'],
    'Backend Developer': ['Programming / Software Development', 'Database'],
    'Mobile App Developer': ['Programming / Software Development'],
    'Game Developer': ['Programming / Software Development'],
    
    # Data & AI
    'Data Scientist': ['Data Science / Data Analytics', 'AI / Machine Learning'],
    'Data Analyst': ['Data Science / Data Analytics'],
    'Machine Learning Engineer': ['AI / Machine Learning', 'Data Science / Data Analytics'],
    'AI Engineer': ['AI / Machine Learning', 'Programming / Software Development'],
    'AI/ML Researcher': ['AI / Machine Learning', 'Data Science / Data Analytics'],
    
    # Cybersecurity & Networking
    'Cybersecurity Analyst': ['Cybersecurity', 'Networking'],
    'Network Engineer': ['Networking', 'Cloud Computing'],
    'Security Architect': ['Cybersecurity', 'Networking'],
    
    # Cloud & Systems
    'Cloud Architect': ['Cloud Computing', 'Networking'],
    'DevOps Engineer': ['Cloud Computing', 'Programming / Software Development'],
    'Systems Administrator': ['Cloud Computing'],
    'Site Reliability Engineer': ['Cloud Computing', 'Programming / Software Development'],
    
    # Database
    'Database Administrator': ['Database'],
    'Data Engineer': ['Database', 'Data Science / Data Analytics'],
}
CAREERS = list(CAREER_DOMAIN_MAPPING.keys())
FEATURE_COLUMNS = ['cgpa', 'avg_marks', 'min_marks', 'max_marks', 'std_marks', 
                   'total_subjects', 'department_id'] + DOMAINS


class CareerRecommender:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.is_loaded = False
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.model_path = os.path.join(self.models_dir, 'career_recommender_model.pkl')
        self.scaler_path = os.path.join(self.models_dir, 'career_scaler.pkl')
        self.encoder_path = os.path.join(self.models_dir, 'career_label_encoder.pkl')
        self.columns_path = os.path.join(self.models_dir, 'career_feature_columns.pkl')
        
        self.load_model()

    def load_model(self):
        """Load trained model and preprocessors"""
        try:
            if all(os.path.exists(p) for p in [self.model_path, self.scaler_path, self.encoder_path]):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.label_encoder = joblib.load(self.encoder_path)
                self.feature_columns = joblib.load(self.columns_path)
                self.is_loaded = True
                print("✅ Model loaded successfully!")
                return True
            else:
                print("ℹ️ Model not found. Using fallback method.")
                return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False

    def fetch_student_data(self, student_id):
        """Fetch student marks and domain scores from Supabase"""
        try:
            marks = supabase.table('student_marks').select('*').eq('student_id', student_id).execute()
            domain_mapping = supabase.table('subject_domain_mapping').select('*').execute()
            
            if not marks.data:
                return None
            
            marks_df = pd.DataFrame(marks.data)
            domain_df = pd.DataFrame(domain_mapping.data)
            
            df = marks_df.merge(domain_df, on='subject_id', how='left')
            
            student = supabase.table('student').select('*').eq('student_id', student_id).execute()
            student_info = student.data[0] if student.data else {}
            
            domain_scores = {}
            for domain in DOMAINS:
                domain_data = df[df['domain'] == domain]
                if len(domain_data) > 0:
                    avg_score = domain_data['marks_obtained'].mean()
                    domain_scores[domain] = round(avg_score, 2)
                else:
                    domain_scores[domain] = 0
            
            marks_col = 'marks_obtained'
            avg_marks = df[marks_col].mean()
            min_marks = df[marks_col].min()
            max_marks = df[marks_col].max()
            std_marks = df[marks_col].std()
            total_subjects = len(df)
            cgpa = avg_marks / 10
            
            return {
                'student_id': student_id,
                'student_name': student_info.get('full_name', 'Student'),
                'roll_no': student_info.get('roll_no', ''),
                'department_id': student_info.get('department_id', 1),
                'cgpa': round(cgpa, 2),
                'avg_marks': round(avg_marks, 2),
                'min_marks': round(min_marks, 2),
                'max_marks': round(max_marks, 2),
                'std_marks': round(std_marks, 2) if not np.isnan(std_marks) else 0,
                'total_subjects': total_subjects,
                'domain_scores': domain_scores
            }
            
        except Exception as e:
            print(f"❌ Error fetching student data: {e}")
            return None

    def create_student_features(self, student_data):
        if not student_data:
            return None
        
        features = {
            'cgpa': student_data['cgpa'],
            'avg_marks': student_data['avg_marks'],
            'min_marks': student_data['min_marks'],
            'max_marks': student_data['max_marks'],
            'std_marks': student_data['std_marks'],
            'total_subjects': student_data['total_subjects'],
            'department_id': student_data['department_id'],
            **student_data['domain_scores']
        }
        return features

    def predict_career(self, student_id):
        student_data = self.fetch_student_data(student_id)
        if not student_data:
            return "Student not found", 0, None
        
        features = self.create_student_features(student_data)
        if not features:
            return "No data available", 0, None
        
        if not self.is_loaded:
            return self._domain_based_recommendation(student_data)
        
        try:
            feature_vector = np.array([features[col] for col in self.feature_columns]).reshape(1, -1)
            scaled_features = self.scaler.transform(feature_vector)
            
            prediction = self.model.predict(scaled_features)
            career = self.label_encoder.inverse_transform(prediction)[0]
            
            proba = self.model.predict_proba(scaled_features)[0]
            confidence = max(proba) * 100
            
            return career, confidence, student_data
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return self._domain_based_recommendation(student_data)

    def _domain_based_recommendation(self, student_data):
        domain_scores = student_data['domain_scores']
        
        career_scores = {}
        for career, domains in CAREER_DOMAIN_MAPPING.items():
            score = 0
            count = 0
            for domain in domains:
                if domain in domain_scores:
                    score += domain_scores[domain]
                    count += 1
            if count > 0:
                career_scores[career] = score / count
            else:
                career_scores[career] = 0
        
        best_career = max(career_scores, key=career_scores.get)
        confidence = (career_scores[best_career] / 100) * 100 if career_scores[best_career] > 0 else 0
        
        return best_career, min(confidence, 95), student_data

    # ============================================
    # ✅ STORE PREDICTION METHOD - ADD THIS
    # ============================================
    def store_prediction(self, student_id, career, confidence, student_data):
        """Store career prediction in Supabase"""
        try:
            domain_scores = student_data.get('domain_scores', {}) if student_data else {}
            
            sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
            top_domains = sorted_domains[:3] if len(sorted_domains) >= 3 else sorted_domains
            
            top_domains_json = [
                {'domain': d[0], 'score': float(d[1])} for d in top_domains
            ]
            
            existing = supabase.table('career_predictions')\
                .select('prediction_id')\
                .eq('student_id', student_id)\
                .execute()
            
            prediction_data = {
                'student_id': student_id,
                'predicted_career': career,
                'confidence': float(confidence),
                'domain_scores': domain_scores,
                'student_cgpa': float(student_data.get('cgpa', 0)) if student_data else 0,
                'avg_marks': float(student_data.get('avg_marks', 0)) if student_data else 0,
                'total_subjects': int(student_data.get('total_subjects', 0)) if student_data else 0,
                'top_domains': top_domains_json,
                'updated_at': datetime.now().isoformat()
            }
            
            if existing.data:
                result = supabase.table('career_predictions')\
                    .update(prediction_data)\
                    .eq('student_id', student_id)\
                    .execute()
                print(f"✅ Updated prediction for student {student_id}")
            else:
                prediction_data['created_at'] = datetime.now().isoformat()
                result = supabase.table('career_predictions')\
                    .insert(prediction_data)\
                    .execute()
                print(f"✅ Stored prediction for student {student_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing prediction: {e}")
            return False


# Initialize
recommender = CareerRecommender()


def get_career_recommendation(student_id):
    return recommender.predict_career(student_id)


def store_career_prediction(student_id):
    career, confidence, student_data = recommender.predict_career(student_id)
    if career and career != "Student not found":
        return recommender.store_prediction(student_id, career, confidence, student_data)
    return False