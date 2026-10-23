from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .services.predictor import SkillPredictor
from core.supabase_client import supabase

predictor = SkillPredictor()


# ============================================
# SKILLS DASHBOARD (Admin View)
# ============================================

def skills_dashboard(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    # Get all students
    try:
        students_res = supabase.table('student').select('*').execute()
        students = students_res.data if hasattr(students_res, 'data') else []
    except:
        students = []
    
    # Get predictions for each student
    student_predictions = []
    for student in students:
        try:
            pred = predictor.predict(student.get('student_id'))
            student_predictions.append({
                'student': student,
                'prediction': pred
            })
        except:
            pass
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'students': students,
        'student_predictions': student_predictions,
        'total_students': len(students),
    }
    return render(request, 'skills_dashboard.html', context)


# ============================================
# STUDENT SKILL PROFILE (Student View)
# ============================================

def student_skill_profile(request, student_id):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    # Fetch student details
    try:
        student_res = supabase.table('student').select('*').eq('student_id', student_id).execute()
        student = student_res.data[0] if student_res.data else None
    except:
        student = None
    
    if not student:
        messages.error(request, 'Student not found!')
        return redirect('admin_dashboard')
    
    # Predict skills
    prediction = predictor.predict(student_id)
    
    context = {
        'student': student,
        'prediction': prediction,
        'admin_name': request.session.get('username', 'Admin'),
    }
    return render(request, 'student_skill_profile.html', context)


# ============================================
# SKILL PREDICTION API
# ============================================

def predict_api(request, student_id):
    """API endpoint for skills prediction"""
    try:
        prediction = predictor.predict(student_id)
        return JsonResponse({'status': 'success', 'data': prediction})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})