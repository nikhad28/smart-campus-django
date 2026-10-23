# core/management/commands/train_model.py
from django.core.management.base import BaseCommand
import pandas as pd
import numpy as np
import joblib
import os
from supabase import create_client
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Supabase connection
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Domain mapping (as per your table)
DOMAINS = [
    'Programming / Software Development',
    'Database',
    'Networking',
    'AI / Machine Learning',
    'Data Science / Data Analytics',
    'Cybersecurity',
    'Cloud Computing'
]

# Career to domain mapping
CAREER_DOMAIN_MAPPING = {
    'Software Developer': ['Programming / Software Development', 'Database'],
    'Full Stack Developer': ['Programming / Software Development', 'Database'],
    'Data Scientist': ['Data Science / Data Analytics', 'AI / Machine Learning'],
    'Data Analyst': ['Data Science / Data Analytics'],
    'Machine Learning Engineer': ['AI / Machine Learning', 'Data Science / Data Analytics'],
    'AI Engineer': ['AI / Machine Learning', 'Programming / Software Development'],
    'Cybersecurity Analyst': ['Cybersecurity', 'Networking'],
    'Database Administrator': ['Database'],
    'Network Engineer': ['Networking', 'Cloud Computing'],
    'Cloud Architect': ['Cloud Computing', 'Networking'],
    'Systems Administrator': ['Cloud Computing'],
    'AI/ML Researcher': ['AI / Machine Learning', 'Data Science / Data Analytics'],
    'DevOps Engineer': ['Cloud Computing', 'Programming / Software Development'],
}

CAREERS = list(CAREER_DOMAIN_MAPPING.keys())
FEATURE_COLUMNS = ['cgpa', 'avg_marks', 'min_marks', 'max_marks', 'std_marks', 
                   'total_subjects', 'department_id'] + DOMAINS


class Command(BaseCommand):
    help = 'Train career recommendation model'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting model training...'))
        
        # Fetch and prepare data
        self.stdout.write('📊 Fetching data from Supabase...')
        df = self.fetch_all_student_data()
        
        if df is None or len(df) == 0:
            self.stdout.write(self.style.ERROR('❌ No data found!'))
            return
        
        self.stdout.write(f'✅ Found {len(df)} students with data')
        
        # Create training dataset
        self.stdout.write('🔧 Creating training dataset...')
        training_data = self.create_training_data(df)
        
        if training_data is None or len(training_data) < 5:
            self.stdout.write(self.style.ERROR('❌ Not enough data to train!'))
            return
        
        # Train model
        self.stdout.write('🧠 Training model...')
        model, scaler, label_encoder = self.train_model(training_data)
        
        if model is None:
            self.stdout.write(self.style.ERROR('❌ Model training failed!'))
            return
        
        # Save model
        self.stdout.write('💾 Saving model...')
        self.save_model(model, scaler, label_encoder)
        
        self.stdout.write(self.style.SUCCESS('✅ Model training complete!'))

    def fetch_all_student_data(self):
        """Fetch all student data with domain scores"""
        try:
            # Fetch all students
            students = supabase.table('student').select('student_id, department_id, full_name').execute()
            
            # Fetch marks and domain mapping
            marks = supabase.table('student_marks').select('*').execute()
            domain_mapping = supabase.table('subject_domain_mapping').select('*').execute()
            
            if not marks.data:
                return None
            
            marks_df = pd.DataFrame(marks.data)
            domain_df = pd.DataFrame(domain_mapping.data)
            students_df = pd.DataFrame(students.data)
            
            # Merge marks with domain mapping
            df = marks_df.merge(domain_df, on='subject_id', how='left')
            
            # Calculate domain scores per student
            student_data = []
            for student_id in students_df['student_id'].unique():
                student_marks = df[df['student_id'] == student_id]
                if len(student_marks) == 0:
                    continue
                
                student_info = students_df[students_df['student_id'] == student_id].iloc[0]
                
                # Domain scores
                domain_scores = {}
                for domain in DOMAINS:
                    domain_data = student_marks[student_marks['domain'] == domain]
                    if len(domain_data) > 0:
                        avg_score = domain_data['marks_obtained'].mean()
                        domain_scores[domain] = round(avg_score, 2)
                    else:
                        domain_scores[domain] = 0
                
                # Overall stats
                avg_marks = student_marks['marks_obtained'].mean()
                min_marks = student_marks['marks_obtained'].min()
                max_marks = student_marks['marks_obtained'].max()
                std_marks = student_marks['marks_obtained'].std()
                total_subjects = len(student_marks)
                cgpa = avg_marks / 10
                
                # Get career label (based on best domain)
                best_domain = max(domain_scores, key=domain_scores.get)
                career_label = self.get_career_from_domain(best_domain, domain_scores)
                
                row = {
                    'student_id': student_id,
                    'department_id': student_info['department_id'],
                    'cgpa': round(cgpa, 2),
                    'avg_marks': round(avg_marks, 2),
                    'min_marks': round(min_marks, 2),
                    'max_marks': round(max_marks, 2),
                    'std_marks': round(std_marks, 2) if not np.isnan(std_marks) else 0,
                    'total_subjects': total_subjects,
                    'career_label': career_label,
                    **domain_scores
                }
                student_data.append(row)
            
            return pd.DataFrame(student_data)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_career_from_domain(self, domain, domain_scores):
        """Get career label from domain scores"""
        best_score = 0
        best_career = 'Software Developer'
        
        for career, domains in CAREER_DOMAIN_MAPPING.items():
            score = 0
            count = 0
            for d in domains:
                if d in domain_scores:
                    score += domain_scores[d]
                    count += 1
            if count > 0:
                avg_score = score / count
                if avg_score > best_score:
                    best_score = avg_score
                    best_career = career
        
        return best_career

    def create_training_data(self, df):
        """Prepare training data"""
        X = df[FEATURE_COLUMNS]
        y = df['career_label']
        
        # Check class distribution
        self.stdout.write(f"📊 Class distribution: {y.value_counts().to_dict()}")
        
        return df

    def train_model(self, df):
        """Train and evaluate models"""
        X = df[FEATURE_COLUMNS]
        y = df['career_label']
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42
        )
        
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'XGBoost': XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
        }
        
        best_model = None
        best_accuracy = 0
        
        self.stdout.write('-' * 60)
        for name, model in models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            self.stdout.write(f'{name}: {accuracy*100:.2f}%')
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model
        
        self.stdout.write('-' * 60)
        self.stdout.write(self.style.SUCCESS(f'🏆 Best Model: {type(best_model).__name__} ({best_accuracy*100:.2f}%)'))
        
        return best_model, scaler, label_encoder

    def save_model(self, model, scaler, label_encoder):
        """Save model files"""
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        joblib.dump(model, os.path.join(models_dir, 'career_recommender_model.pkl'))
        joblib.dump(scaler, os.path.join(models_dir, 'career_scaler.pkl'))
        joblib.dump(label_encoder, os.path.join(models_dir, 'career_label_encoder.pkl'))
        joblib.dump(FEATURE_COLUMNS, os.path.join(models_dir, 'career_feature_columns.pkl'))
        joblib.dump(CAREER_DOMAIN_MAPPING, os.path.join(models_dir, 'career_domain_mapping.pkl'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Models saved to: {models_dir}'))