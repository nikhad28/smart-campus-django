# core/management/commands/predict_all.py
from django.core.management.base import BaseCommand
from core.utils.career_recommender import recommender
from supabase import create_client
import os

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class Command(BaseCommand):
    help = 'Predict and store careers for all students'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Predicting careers for all students...')
        
        # Get all students
        students = supabase.table('student').select('student_id').execute()
        
        success_count = 0
        fail_count = 0
        
        for student in students.data:
            student_id = student['student_id']
            
            try:
                career, confidence, student_data = recommender.predict_career(student_id)
                
                if career and career != "Student not found":
                    stored = recommender.store_prediction(student_id, career, confidence, student_data)
                    if stored:
                        success_count += 1
                        self.stdout.write(f'✅ Student {student_id}: {career}')
                    else:
                        fail_count += 1
                else:
                    fail_count += 1
                    self.stdout.write(f'❌ Student {student_id}: No data')
                    
            except Exception as e:
                fail_count += 1
                self.stdout.write(f'❌ Student {student_id}: Error - {e}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Predictions completed! Success: {success_count}, Failed: {fail_count}'
        ))