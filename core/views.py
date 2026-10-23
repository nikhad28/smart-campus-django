import random
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .supabase_client import supabase
from otp_app.models import OTP
import bcrypt
# core/views.py - Add this import at the top with other imports
from .utils.career_recommender import recommender, get_career_recommendation
# core/views.py
import numpy as np


# ============================================
# INDEX PAGE
# ============================================

def index(request):
    return render(request, 'index.html')


# ============================================
# ADMIN LOGIN
# ============================================

def admin_login(request):
    if request.session.get('logged_in'):
        role = request.session.get('user_role')
        if role == 'admin':
            return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            response = supabase.table('user_account')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if response.data:
                user = response.data[0]
                
                if not user.get('is_active', True):
                    messages.error(request, '❌ Your account is inactive. Contact admin.')
                    return render(request, 'admin_login.html')
                
                role = user.get('role_id')
                password_hash = user.get('password_hash', '')
                
                password_match = False
                try:
                    if password_hash.startswith('$2b$'):
                        password_match = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
                    else:
                        password_match = (password == password_hash)
                except:
                    password_match = (password == password_hash)
                
                if password_match:
                    request.session['logged_in'] = True
                    request.session['user_id'] = user.get('user_id')
                    request.session['username'] = user.get('username')
                    request.session['user_role'] = role
                    
                    messages.success(request, f'Welcome {username}! 🎉')
                    
                    if role == 1:
                        return redirect('admin_dashboard')
                    else:
                        messages.info(request, 'Role-based dashboard coming soon!')
                        return redirect('admin_dashboard')
                else:
                    messages.error(request, '❌ Invalid Password!')
            else:
                messages.error(request, '❌ User not found!')
                
        except Exception as e:
            messages.error(request, f'❌ Database Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'admin_login.html')


def admin_dashboard(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    # Initialize context with default values
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'user_id': request.session.get('user_id'),
        'role': request.session.get('user_role'),
        'total_students': 0,
        'total_tpo': 0,
        'total_faculty': 0,
        'total_hod': 0,
        'pending_count': 0,
        'in_progress_count': 0,
        'resolved_count': 0,
        'dept_wise_data': [0, 0, 0, 0, 0, 0, 0, 0],
        'monthly_data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    
    try:
        # GET ALL STUDENTS
        students_response = supabase.table('student').select('*', count='exact').execute()
        students = students_response.data if hasattr(students_response, 'data') else []
        total_students = len(students)
        
        # Department-wise student count
        dept_counts = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
        monthly_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        for student in students:
            dept_id = student.get('department_id')
            if dept_id in dept_counts:
                dept_counts[dept_id] += 1
            
            # Monthly registration count
            created_at = student.get('created_at')
            if created_at:
                try:
                    # Handle date parsing
                    if 'T' in created_at:
                        month = datetime.fromisoformat(created_at.replace('Z', '+00:00')).month - 1
                    else:
                        month = datetime.strptime(created_at, '%Y-%m-%d').month - 1
                    if 0 <= month < 12:
                        monthly_counts[month] += 1
                except:
                    pass
        
        context['dept_wise_data'] = list(dept_counts.values())
        context['monthly_data'] = monthly_counts
        
        # GET ALL TPO OFFICERS
        tpo_response = supabase.table('tpo').select('*', count='exact').execute()
        tpo_list = tpo_response.data if hasattr(tpo_response, 'data') else []
        total_tpo = len(tpo_list)
        
        # GET ALL FACULTY
        faculty_response = supabase.table('faculty').select('*', count='exact').execute()
        faculty_list = faculty_response.data if hasattr(faculty_response, 'data') else []
        total_faculty = len(faculty_list)
        
        # GET ALL HOD
        hod_response = supabase.table('hod').select('*', count='exact').execute()
        hod_list = hod_response.data if hasattr(hod_response, 'data') else []
        total_hod = len(hod_list)
        
        # GET INFRASTRUCTURE ISSUES
        issues_response = supabase.table('infrastructure_issues').select('*', count='exact').execute()
        issues = issues_response.data if hasattr(issues_response, 'data') else []
        
        pending_count = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        in_progress_count = sum(1 for i in issues if i.get('status', '').lower() == 'in_progress')
        resolved_count = sum(1 for i in issues if i.get('status', '').lower() == 'resolved')
        
        context.update({
            'total_students': total_students,
            'total_tpo': total_tpo,
            'total_faculty': total_faculty,
            'total_hod': total_hod,
            'pending_count': pending_count,
            'in_progress_count': in_progress_count,
            'resolved_count': resolved_count,
        })
        
    except Exception as e:
        print(f"Dashboard Error: {e}")
    
    return render(request, 'admin_dashboard.html', context)

# ============================================
# ADMIN STUDENTS - View all students
# ============================================
def admin_students(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_students': 0,
        'active_students': 0,
        'inactive_students': 0,
        'pending_verification': 0,
        'students': [],
        'total_tpo': 0,
        'total_faculty': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        # ✅ GET ALL STUDENTS (Without any filter)
        response = supabase.table('student').select('*').execute()
        students = response.data if hasattr(response, 'data') else []
        context['students'] = students
        context['total_students'] = len(students)
        
        print(f"✅ Total students in admin_students: {len(students)}")  # Debug line
        
        # Active/Inactive count (if is_active column exists)
        context['active_students'] = sum(1 for s in students if s.get('is_active', False))
        context['inactive_students'] = sum(1 for s in students if not s.get('is_active', True))
        
        # For sidebar counts
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin Students Error: {e}")
    
    return render(request, 'admin_students.html', context)
# ============================================
# ADMIN FACULTY - View all faculty
# ============================================

def admin_faculty(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_faculty': 0,
        'active_faculty': 0,
        'departments_count': 0,
        'faculties': [],
        # Sidebar variables
        'total_students': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        # Get all faculty
        response = supabase.table('faculty').select('*').execute()
        faculties = response.data if hasattr(response, 'data') else []
        context['faculties'] = faculties
        context['total_faculty'] = len(faculties)
        context['active_faculty'] = sum(1 for f in faculties if f.get('is_active', False))
        
        # Unique departments
        depts = set(f.get('department') for f in faculties if f.get('department'))
        context['departments_count'] = len(depts)
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin Faculty Error: {e}")
    
    return render(request, 'admin_faculty.html', context)


# ============================================
# ADMIN ADD FACULTY (Modal Form Submit)
# ============================================

def admin_add_faculty(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        data = {
            'employee_id': request.POST.get('employee_id') or None,
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email') or None,
            'phone': request.POST.get('phone') or None,
            'designation': request.POST.get('designation') or None,
            'department': request.POST.get('department') or None,
            'is_active': request.POST.get('is_active') == 'true',
        }
        
        # Remove None/empty values
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        # Check required fields
        if not data.get('full_name'):
            messages.error(request, '❌ Full Name is required!')
            return redirect('admin_dashboard')
        
        try:
            supabase.table('faculty').insert(data).execute()
            messages.success(request, '✅ Faculty added successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return redirect('admin_dashboard')


# ============================================
# ADMIN UPDATE FACULTY STATUS (Inline)
# ============================================

@csrf_exempt
def admin_update_faculty_status(request, faculty_id):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        is_active = request.POST.get('is_active') == 'true'
        try:
            supabase.table('faculty').update({'is_active': is_active}).eq('faculty_id', faculty_id).execute()
            messages.success(request, '✅ Faculty status updated successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    return redirect('admin_faculty')


# ============================================
# ADMIN UPDATE FACULTY (Full Edit)
# ============================================

def admin_update_faculty(request, faculty_id):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    # Get faculty details
    response = supabase.table('faculty').select('*').eq('faculty_id', faculty_id).execute()
    faculty = response.data[0] if response.data else None
    
    if not faculty:
        messages.error(request, '❌ Faculty not found!')
        return redirect('admin_faculty')
    
    if request.method == 'POST':
        data = {
            'employee_id': request.POST.get('employee_id') or None,
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email') or None,
            'phone': request.POST.get('phone') or None,
            'designation': request.POST.get('designation') or None,
            'department': request.POST.get('department') or None,
            'is_active': request.POST.get('is_active') == 'true',
        }
        
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        if not data.get('full_name'):
            messages.error(request, '❌ Full Name is required!')
            return render(request, 'admin_edit_faculty.html', {'faculty': faculty})
        
        try:
            supabase.table('faculty').update(data).eq('faculty_id', faculty_id).execute()
            messages.success(request, '✅ Faculty updated successfully!')
            return redirect('admin_faculty')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    # Get sidebar counts
    context = {
        'faculty': faculty,
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
    except:
        pass
    
    return render(request, 'admin_edit_faculty.html', context)


# ============================================
# ADMIN DELETE FACULTY
# ============================================

@csrf_exempt
def admin_delete_faculty(request, faculty_id):
    if not request.session.get('logged_in'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            supabase.table('faculty').delete().eq('faculty_id', faculty_id).execute()
            messages.success(request, '✅ Faculty deleted successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    return redirect('admin_faculty')
# ============================================
# ADMIN TPO - View all TPO officers
# ============================================

def admin_tpo(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_tpo': 0,
        'active_tpo': 0,
        'tpo_list': [],
        # Sidebar variables
        'total_students': 0,
        'total_faculty': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        # Get all TPO
        response = supabase.table('tpo').select('*').execute()
        tpo_list = response.data if hasattr(response, 'data') else []
        context['tpo_list'] = tpo_list
        context['total_tpo'] = len(tpo_list)
        context['active_tpo'] = sum(1 for t in tpo_list if t.get('is_active', False))
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin TPO Error: {e}")
    
    return render(request, 'admin_tpo.html', context)


# ============================================
# ADMIN HOD - View all HODs
# ============================================

def admin_hod(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_hod': 0,
        'active_hod': 0,
        'departments_hod': 0,
        'hod_list': [],
        # Sidebar variables
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'pending_count': 0,
    }
    
    try:
        # Get all HOD
        response = supabase.table('hod').select('*').execute()
        hod_list = response.data if hasattr(response, 'data') else []
        context['hod_list'] = hod_list
        context['total_hod'] = len(hod_list)
        context['active_hod'] = sum(1 for h in hod_list if h.get('is_active', False))
        
        # Unique departments
        depts = set(h.get('department') for h in hod_list if h.get('department'))
        context['departments_hod'] = len(depts)
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin HOD Error: {e}")
    
    return render(request, 'admin_hod.html', context)


# ============================================
# ADMIN USERS - View all users
# ============================================

def admin_users(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_users': 0,
        'users': [],
        # Sidebar variables
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        # Get all users
        response = supabase.table('user_account').select('*').execute()
        users = response.data if hasattr(response, 'data') else []
        context['users'] = users
        context['total_users'] = len(users)
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin Users Error: {e}")
    
    return render(request, 'admin_users.html', context)


# ============================================
# ADMIN REPORTS - Reports page
# ============================================
def admin_reports(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_users': 0,
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
        'active_students': 0,
        'inactive_students': 0,
        'dept_wise_data': [0, 0, 0, 0, 0, 0, 0, 0],
        'monthly_data': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    
    try:
        # GET ALL USERS
        user_res = supabase.table('user_account').select('*', count='exact').execute()
        context['total_users'] = len(user_res.data) if hasattr(user_res, 'data') else 0
        
        # GET ALL STUDENTS
        student_res = supabase.table('student').select('*', count='exact').execute()
        students = student_res.data if hasattr(student_res, 'data') else []
        context['total_students'] = len(students)
        
        # Active/Inactive Students
        context['active_students'] = sum(1 for s in students if s.get('is_active', False))
        context['inactive_students'] = sum(1 for s in students if not s.get('is_active', True))
        
        # Department-wise student count
        dept_counts = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0}
        monthly_counts = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        for student in students:
            dept_id = student.get('department_id')
            if dept_id in dept_counts:
                dept_counts[dept_id] += 1
            
            created_at = student.get('created_at')
            if created_at:
                try:
                    if 'T' in created_at:
                        month = datetime.fromisoformat(created_at.replace('Z', '+00:00')).month - 1
                    else:
                        month = datetime.strptime(created_at, '%Y-%m-%d').month - 1
                    if 0 <= month < 12:
                        monthly_counts[month] += 1
                except:
                    pass
        
        context['dept_wise_data'] = list(dept_counts.values())
        context['monthly_data'] = monthly_counts
        
        # GET FACULTY
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        # GET TPO
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        # GET HOD
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        # GET ISSUES
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin Reports Error: {e}")
    
    return render(request, 'admin_reports.html', context)

# ============================================
# ADMIN PROFILE - Admin profile page
# ============================================

def admin_profile(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'user_id': request.session.get('user_id'),
        'role': request.session.get('user_role'),
        'joined_date': 'N/A',
        # Sidebar variables
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
    }
    
    try:
        # Get joined date from database
        if request.session.get('user_id'):
            user_res = supabase.table('user_account').select('created_at').eq('user_id', request.session.get('user_id')).execute()
            if user_res.data:
                context['joined_date'] = user_res.data[0].get('created_at', 'N/A')
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        
    except Exception as e:
        print(f"Admin Profile Error: {e}")
    
    return render(request, 'admin_profile.html', context)


# ============================================
# ADMIN LOGOUT
# ============================================

def admin_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('admin_login')
# ============================================
# ADMIN ADD STUDENT (Modal Form Submit)
# ============================================

def admin_add_student(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        data = {
            'student_id': request.POST.get('student_id'),
            'roll_no': request.POST.get('roll_no'),
            'full_name': request.POST.get('full_name'),
            'gender': request.POST.get('gender'),
            'dob': request.POST.get('dob'),
            'whatsapp_no': request.POST.get('whatsapp_no'),
            'admission_year': request.POST.get('admission_year'),
            'department_id': request.POST.get('department_id'),
            'semester_id': request.POST.get('semester_id'),
            'email': request.POST.get('email') or None,
            'division_id': request.POST.get('division_id') or None,
            'parent_id': request.POST.get('parent_id') or None,
        }
        
        # Remove None/empty values
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        # Check required fields
        if not data.get('department_id'):
            messages.error(request, '❌ Department ID is required!')
            return redirect('admin_dashboard')
        
        if not data.get('semester_id'):
            messages.error(request, '❌ Semester ID is required!')
            return redirect('admin_dashboard')
        
        try:
            supabase.table('student').insert(data).execute()
            messages.success(request, '✅ Student added successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return redirect('admin_dashboard')
# ============================================
# ADMIN ADD FACULTY (Modal Form Submit)
# ============================================

def admin_add_faculty(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        data = {
            'employee_id': request.POST.get('employee_id') or None,
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email') or None,
            'phone': request.POST.get('phone') or None,
            'designation': request.POST.get('designation') or None,
            'department_id': request.POST.get('department_id'),
        }
        
        # Remove None/empty values
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        # Check required fields
        if not data.get('full_name'):
            messages.error(request, '❌ Full Name is required!')
            return redirect('admin_dashboard')
        
        if not data.get('department_id'):
            messages.error(request, '❌ Department ID is required!')
            return redirect('admin_dashboard')
        
        try:
            supabase.table('faculty').insert(data).execute()
            messages.success(request, '✅ Faculty added successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return redirect('admin_dashboard')
# ============================================
# ADMIN ADD TPO (Modal Form Submit - Dashboard)
# ============================================

def admin_add_tpo(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        data = {
            'user_id': request.POST.get('user_id'),
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'department': request.POST.get('department') or None,
            'password_hash': request.POST.get('password_hash'),
            'is_active': request.POST.get('is_active') == 'true',
        }
        
        # Remove None/empty values
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        # Check required fields
        if not data.get('user_id'):
            messages.error(request, '❌ User ID is required!')
            return redirect('admin_dashboard')
        
        if not data.get('full_name'):
            messages.error(request, '❌ Full Name is required!')
            return redirect('admin_dashboard')
        
        if not data.get('email'):
            messages.error(request, '❌ Email is required!')
            return redirect('admin_dashboard')
        
        if not data.get('phone'):
            messages.error(request, '❌ Phone is required!')
            return redirect('admin_dashboard')
        
        if not data.get('password_hash'):
            messages.error(request, '❌ Password is required!')
            return redirect('admin_dashboard')
        
        try:
            supabase.table('tpo').insert(data).execute()
            messages.success(request, '✅ TPO added successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return redirect('admin_dashboard')

# ============================================
# ADMIN ADD HOD (Modal Form Submit - No Password)
# ============================================

def admin_add_hod(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    if request.method == 'POST':
        data = {
            'user_id': request.POST.get('user_id'),
            'full_name': request.POST.get('full_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone') or None,
            'department': request.POST.get('department') or None,
            'is_active': request.POST.get('is_active') == 'true',
        }
        
        # Remove None/empty values
        data = {k: v for k, v in data.items() if v is not None and v != ''}
        
        # Check required fields
        if not data.get('user_id'):
            messages.error(request, '❌ User ID is required!')
            return redirect('admin_dashboard')
        
        if not data.get('full_name'):
            messages.error(request, '❌ Full Name is required!')
            return redirect('admin_dashboard')
        
        if not data.get('email'):
            messages.error(request, '❌ Email is required!')
            return redirect('admin_dashboard')
        
        try:
            supabase.table('hod').insert(data).execute()
            messages.success(request, '✅ HOD added successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return redirect('admin_dashboard')
# ============================================
# GENERATE OTP
# ============================================

def generate_otp():
    return str(random.randint(100000, 999999))


# ============================================
# STUDENT LOGIN — STEP 1: Send OTP
# ============================================

def student_login(request):
    if request.session.get('student_logged_in'):
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        whatsapp_no = request.POST.get('whatsapp_no')
        
        if not whatsapp_no:
            messages.error(request, '❌ Please enter your WhatsApp number!')
            return render(request, 'student_login.html')
        
        try:
            response = supabase.table('student')\
                .select('*')\
                .eq('whatsapp_no', whatsapp_no)\
                .execute()
            
            if response.data:
                student = response.data[0]
                otp_code = generate_otp()
                
                OTP.objects.filter(phone_number=whatsapp_no, is_verified=False).delete()
                OTP.objects.create(
                    phone_number=whatsapp_no,
                    otp_code=otp_code,
                    expires_at=timezone.now() + timedelta(minutes=5)
                )
                
                print(f"📱 OTP for {student['full_name']} ({whatsapp_no}): {otp_code}")
                
                request.session['student_whatsapp'] = whatsapp_no
                request.session['student_name'] = student['full_name']
                request.session['student_id'] = student['student_id']
                request.session['student_email'] = student.get('email', '')
                
                messages.success(request, f'✅ OTP sent to {whatsapp_no}! Check console.')
                return redirect('student_verify_otp')
            else:
                messages.error(request, '❌ WhatsApp number not registered!')
                
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'student_login.html')


# ============================================
# STUDENT LOGIN — STEP 2: Verify OTP
# ============================================

def student_verify_otp(request):
    if not request.session.get('student_whatsapp'):
        messages.error(request, '❌ Please request OTP first!')
        return redirect('student_login')
    
    whatsapp_no = request.session.get('student_whatsapp')
    student_name = request.session.get('student_name', 'Student')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        if not otp_code:
            messages.error(request, '❌ Please enter OTP!')
            return render(request, 'student_verify_otp.html', {
                'whatsapp_no': whatsapp_no,
                'student_name': student_name
            })
        
        try:
            otp_record = OTP.objects.filter(
                phone_number=whatsapp_no,
                otp_code=otp_code,
                is_verified=False
            ).latest('created_at')
            
            if otp_record.is_expired():
                messages.error(request, '❌ OTP has expired! Please request again.')
                return redirect('student_login')
            
            otp_record.is_verified = True
            otp_record.save()
            
            request.session['student_logged_in'] = True
            messages.success(request, f'🎉 Welcome {student_name}!')
            return redirect('student_dashboard')
            
        except OTP.DoesNotExist:
            messages.error(request, '❌ Invalid OTP! Please try again.')
    
    return render(request, 'student_verify_otp.html', {
        'whatsapp_no': whatsapp_no,
        'student_name': student_name
    })

# ============================================
# STUDENT DASHBOARD (With Jobs)
# ============================================

def student_dashboard(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    whatsapp_no = request.session.get('student_whatsapp')
    
    try:
        jobs_response = supabase.table('tpo_jobs')\
            .select('*, company:company_id(company_name, company_website, logo_url)')\
            .eq('is_active', True)\
            .execute()
        active_jobs = jobs_response.data if hasattr(jobs_response, 'data') else []
        
        apps_response = supabase.table('tpo_placements')\
            .select('*, job:job_id(job_title, company_id(company_name))')\
            .eq('student_id', student_id)\
            .execute()
        my_applications = apps_response.data if hasattr(apps_response, 'data') else []
        
        applied_job_ids = [app['job_id'] for app in my_applications]
        total_applied = len(my_applications)
        
    except Exception as e:
        active_jobs = []
        my_applications = []
        applied_job_ids = []
        total_applied = 0
        print(f"Error: {e}")
    
    context = {
        'student_name': student_name,
        'student_id': student_id,  # <-- YEH PEHLE SE HAI, LEKIN...
        'whatsapp_no': whatsapp_no,
        'active_jobs': active_jobs,
        'my_applications': my_applications,
        'applied_job_ids': applied_job_ids,
        'total_applied': total_applied,
    }
    
    return render(request, 'student_dashboard.html', context)


# ============================================
# STUDENT APPLY FOR JOB — WITH FORM
# ============================================

def student_apply_job(request, job_id):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    student_email = request.session.get('student_email', '')
    student_phone = request.session.get('student_whatsapp', '')
    
    # Get job details
    job_response = supabase.table('tpo_jobs').select('*, company:company_id(company_name)').eq('id', job_id).execute()
    job = job_response.data[0] if job_response.data else None
    
    if not job:
        messages.error(request, '❌ Job not found!')
        return redirect('student_dashboard')
    
    # Check if already applied
    existing = supabase.table('tpo_placements')\
        .select('*')\
        .eq('job_id', job_id)\
        .eq('student_id', student_id)\
        .execute()
    
    if existing.data:
        messages.warning(request, '⚠️ You have already applied for this job!')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        resume_link = request.POST.get('resume_link', '')
        
        if not full_name or not email or not phone:
            messages.error(request, '❌ Please fill all required fields!')
            return render(request, 'student_apply_form.html', {
                'job': job,
                'student_name': student_name,
                'student_email': student_email,
                'student_phone': student_phone,
            })
        
        # ✅ Resume link optional — None if empty
        if not resume_link:
            resume_link = None
        
        data = {
            'job_id': job_id,
            'student_id': student_id,
            'student_name': full_name,
            'student_email': email,
            'student_phone': phone,
            'resume_url': resume_link,
            'status': 'applied'
        }
        
        try:
            supabase.table('tpo_placements').insert(data).execute()
            messages.success(request, '✅ Application submitted successfully!')
            
            if job.get('application_link'):
                return redirect(job['application_link'])
            else:
                return redirect('student_dashboard')
                
        except Exception as e:
            messages.error(request, f'❌ Error submitting application: {e}')
            return render(request, 'student_apply_form.html', {
                'job': job,
                'student_name': full_name,
                'student_email': email,
                'student_phone': phone,
            })
    
    context = {
        'job': job,
        'student_name': student_name,
        'student_email': student_email,
        'student_phone': student_phone,
        'student_id': student_id,
    }
    
    return render(request, 'student_apply_form.html', context)


# ============================================
# STUDENT PROFILE
# ============================================

def student_profile(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    whatsapp_no = request.session.get('student_whatsapp')
    student_email = request.session.get('student_email', '')
    
    # Fetch student from Supabase
    try:
        response = supabase.table('student').select('*').eq('student_id', student_id).execute()
        student = response.data[0] if response.data else {}
    except:
        student = {}
    
    context = {
        'student_name': student_name,
        'student_id': student_id,
        'whatsapp_no': whatsapp_no,
        'student_email': student_email,
        'student': student,
    }
    return render(request, 'student_profile.html', context)


# ============================================
# STUDENT MY COURSES
# ============================================

def student_my_courses(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    whatsapp_no = request.session.get('student_whatsapp')
    
    try:
        student_res = supabase.table('student').select('semester_id').eq('student_id', student_id).execute()
        current_semester = student_res.data[0].get('semester_id', 3) if student_res.data else 3
        
        subjects_res = supabase.table('subject')\
            .select('*')\
            .eq('semester_id', current_semester)\
            .execute()
        courses = subjects_res.data if hasattr(subjects_res, 'data') else []
        
    except Exception as e:
        print(f"Error: {e}")
        current_semester = 3
        courses = []
    
    context = {
        'student_name': student_name,
        'student_id': student_id,
        'whatsapp_no': whatsapp_no,
        'courses': courses,
        'total_courses': len(courses),
        'current_semester': current_semester,
    }
    return render(request, 'student_my_courses.html', context)


# ============================================
# STUDENT RESULTS (FIXED CGPA)
# ============================================

def student_results(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    whatsapp_no = request.session.get('student_whatsapp')
    
    try:
        marks_res = supabase.table('student_marks')\
            .select('*, subject:subject_id(*)')\
            .eq('student_id', student_id)\
            .execute()
        
        marks_data = marks_res.data if hasattr(marks_res, 'data') else []
        
        results = []
        total_credits = 0
        total_points = 0
        subject_marks = {}
        
        for mark in marks_data:
            subject = mark.get('subject', {})
            subject_code = subject.get('subject_code', '')
            subject_name = subject.get('subject_name', 'Unknown')
            credits = subject.get('credits', 3)
            marks = mark.get('marks_obtained', 0)
            
            if subject_code not in subject_marks or marks > subject_marks[subject_code]['marks']:
                subject_marks[subject_code] = {
                    'subject_code': subject_code,
                    'subject_name': subject_name,
                    'marks': marks,
                    'credits': credits,
                    'grade': mark.get('grade', '-'),
                    'semester': subject.get('semester_id', 0),
                }
        
        for subj_code, data in subject_marks.items():
            results.append({
                'subject_code': data['subject_code'],
                'subject_name': data['subject_name'],
                'marks': data['marks'],
                'grade': data['grade'],
                'credits': data['credits'],
                'semester': data['semester'],
            })
            total_credits += data['credits']
            total_points += data['marks'] * data['credits']
        
        cgpa = round(total_points / (total_credits * 10), 2) if total_credits > 0 else 0
        
    except Exception as e:
        print(f"Error: {e}")
        results = []
        cgpa = 0
        total_credits = 0
    
    context = {
        'student_name': student_name,
        'student_id': student_id,
        'whatsapp_no': whatsapp_no,
        'results': results,
        'cgpa': cgpa,
        'total_credits': total_credits,
    }
    return render(request, 'student_results.html', context)

# ============================================
# STUDENT PROFILE (Personal Info)
# ============================================

def student_profile(request):
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    whatsapp_no = request.session.get('student_whatsapp')
    student_email = request.session.get('student_email', '')
    
    try:
        # Fetch student from Supabase with semester info
        response = supabase.table('student')\
            .select('*, semester:semester_id(*)')\
            .eq('student_id', student_id)\
            .execute()
        student = response.data[0] if response.data else {}
    except:
        student = {}
    
    context = {
        'student_name': student_name,
        'student_id': student_id,
        'whatsapp_no': whatsapp_no,
        'student_email': student_email,
        'student': student,
        'semester': student.get('semester', {}),
    }
    return render(request, 'student_profile.html', context)
def student_skill_profile(request):
    # Session se student_id lo
    student_id = request.session.get('student_id')
    
    if not student_id:
        return redirect('/student-login/')
    
    # Student fetch karo
    try:
        student_res = supabase.table('student').select('*').eq('student_id', student_id).execute()
        student = student_res.data[0] if student_res.data else None
    except:
        student = None
    
    if not student:
        return redirect('/student-dashboard/')
    
    # Prediction
    prediction = {
        'top_skills': ['Python', 'Communication', 'Teamwork'],
        'recommended_careers': ['Software Developer', 'Data Analyst'],
        'skill_gap': ['Machine Learning', 'Cloud Computing']
    }
    
    context = {
        'student': student,
        'student_name': student.get('full_name', 'Student'),
        'student_email': student.get('email', ''),
        'student_roll': student.get('roll_no', ''),
        'top_skills': prediction.get('top_skills', []),
        'recommended_careers': prediction.get('recommended_careers', []),
        'skill_gap': prediction.get('skill_gap', []),
    }
    
    return render(request, 'student_skill_profile.html', context)
def career_recommendation(request):
    """Career Recommendation page with all subjects display"""
    
    # Check if student is logged in
    if not request.session.get('student_logged_in'):
        return redirect('student_login')
    
    student_id = request.session.get('student_id')
    student_name = request.session.get('student_name', 'Student')
    
    if not student_id:
        messages.error(request, 'Student not found! Please login again.')
        return redirect('student_login')
    
    # Fetch all subjects with marks for this student
    from supabase import create_client
    import os
    import pandas as pd
    
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch student marks with subject details
    marks = supabase.table('student_marks')\
        .select('*, subject:subject_id(*)')\
        .eq('student_id', student_id)\
        .order('examination_id')\
        .execute()
    
    subject_marks = []
    domain_scores = {}
    
    if marks.data:
        # Group by subject
        for record in marks.data:
            subject = record.get('subject', {})
            subject_marks.append({
                'subject_id': record.get('subject_id'),
                'subject_name': subject.get('subject_name', 'Unknown'),
                'subject_code': subject.get('subject_code', ''),
                'marks_obtained': record.get('marks_obtained', 0),
                'grade': record.get('grade', ''),
                'examination_id': record.get('examination_id', 0),
                'domain': record.get('domain', '')
            })
        
        # Get domain scores
        student_data = recommender.fetch_student_data(student_id)
        if student_data:
            domain_scores = student_data.get('domain_scores', {})
    
    # Get domain mapping for skill analysis
    domain_mapping = recommender.domain_mapping if hasattr(recommender, 'domain_mapping') else {}
    
    context = {
        'student_name': student_name,
        'student_id': student_id,
        'subject_marks': subject_marks,
        'domain_scores': domain_scores,
        'domain_mapping': domain_mapping,
        'total_subjects': len(subject_marks),
        'page_title': 'Career Recommendation - AIKTC'
    }
    
    return render(request, 'career_recommendation.html', context)

# core/views.py - Replace your get_career_prediction_ajax with this

def get_career_prediction_ajax(request):
    """AJAX endpoint for career prediction"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        
        if not student_id:
            return JsonResponse({'error': 'Student ID required'}, status=400)
        
        # Get prediction
        career, confidence, student_data = get_career_recommendation(student_id)
        
        # Convert numpy types
        def convert(obj):
            if isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            return obj
        
        domain_scores = student_data.get('domain_scores', {}) if student_data else {}
        domain_scores = convert(domain_scores)
        
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        top_domains = sorted_domains[:3] if len(sorted_domains) >= 3 else sorted_domains
        
        # ============================================
        # ✅ SIRF YEH CHANGE HAI - BAAS ITNA KARO
        # ============================================
        # Best domain se career match karo
        if top_domains and len(top_domains) > 0:
            best_domain = top_domains[0][0]
            best_score = top_domains[0][1]
            
            # Domain se career map karo
            domain_to_career = {
                'Programming / Software Development': 'Software Developer',
                'Database': 'Database Administrator',
                'Networking': 'Network Engineer',
                'AI / Machine Learning': 'AI Engineer',
                'Data Science / Data Analytics': 'Data Scientist',
                'Cybersecurity': 'Cybersecurity Analyst',
                'Cloud Computing': 'Cloud Architect'
            }
            
            # Agar domain mapping mein hai toh career set karo
            if best_domain in domain_to_career:
                career = domain_to_career[best_domain]
                confidence = min(best_score / 100 * 100, 95)
        # ============================================
        
        # Store prediction in database
        if career and career != "Student not found":
            store_success = recommender.store_prediction(student_id, career, confidence, student_data)
        
        response = {
            'success': True,
            'predicted_career': str(career),
            'confidence': float(confidence),
            'domain_scores': domain_scores,
            'top_domains': [
                {'domain': str(d[0]), 'score': float(d[1])} for d in top_domains
            ],
            'student_data': {
                'cgpa': float(student_data.get('cgpa', 0)) if student_data else 0,
                'avg_marks': float(student_data.get('avg_marks', 0)) if student_data else 0,
                'total_subjects': int(student_data.get('total_subjects', 0)) if student_data else 0
            },
            'best_domain': top_domains[0][0] if top_domains else None
        }
        
        return JsonResponse(response)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
    

# ============================================
# STUDENT LOGOUT
# ============================================

def student_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('student_login')


# ============================================
# TPO LOGIN
# ============================================

def tpo_login(request):
    if request.session.get('tpo_logged_in'):
        return redirect('tpo_dashboard')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        
        if not user_id or not password:
            messages.error(request, '❌ Please enter both User ID and Password!')
            return render(request, 'tpo_login.html')
        
        try:
            response = supabase.table('tpo')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data:
                tpo = response.data[0]
                
                if not tpo.get('is_active', True):
                    messages.error(request, '❌ Your account is inactive. Contact admin.')
                    return render(request, 'tpo_login.html')
                
                if tpo.get('password_hash') == password:
                    request.session['tpo_logged_in'] = True
                    request.session['tpo_id'] = tpo.get('tpo_id')
                    request.session['tpo_user_id'] = tpo.get('user_id')
                    request.session['tpo_name'] = tpo.get('full_name')
                    request.session['tpo_department'] = tpo.get('department')
                    
                    messages.success(request, f'🎉 Welcome {tpo["full_name"]}!')
                    return redirect('tpo_dashboard')
                else:
                    messages.error(request, '❌ Invalid Password!')
            else:
                messages.error(request, '❌ User ID not found!')
                
        except Exception as e:
            messages.error(request, f'❌ Database Error: {e}')
            print(f"Error: {e}")
    
    return render(request, 'tpo_login.html')


# ============================================
# TPO DASHBOARD
# ============================================

def tpo_dashboard(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    tpo_id = request.session.get('tpo_id')
    
    try:
        companies = supabase.table('tpo_companies').select('*', count='exact').eq('tpo_id', tpo_id).execute()
        total_companies = companies.count if hasattr(companies, 'count') else len(companies.data)
        
        jobs = supabase.table('tpo_jobs').select('*', count='exact').execute()
        total_jobs = jobs.count if hasattr(jobs, 'count') else len(jobs.data)
        
        active_jobs = supabase.table('tpo_jobs').select('*', count='exact').eq('is_active', True).execute()
        active_count = active_jobs.count if hasattr(active_jobs, 'count') else len(active_jobs.data)
        
        applications = supabase.table('tpo_placements').select('*', count='exact').execute()
        total_applications = applications.count if hasattr(applications, 'count') else len(applications.data)
        
        recent_jobs = supabase.table('tpo_jobs').select('*').order('created_at', desc=True).limit(5).execute()
        recent_apps = supabase.table('tpo_placements').select('*').order('applied_at', desc=True).limit(5).execute()
        
    except Exception as e:
        total_companies = 0
        total_jobs = 0
        active_count = 0
        total_applications = 0
        recent_jobs = []
        recent_apps = []
        print(f"Error: {e}")
    
    context = {
        'tpo_name': request.session.get('tpo_name', 'TPO'),
        'tpo_id': tpo_id,
        'total_companies': total_companies,
        'total_jobs': total_jobs,
        'active_jobs': active_count,
        'total_applications': total_applications,
        'recent_jobs': recent_jobs.data if hasattr(recent_jobs, 'data') else [],
        'recent_applications': recent_apps.data if hasattr(recent_apps, 'data') else [],
    }
    
    return render(request, 'tpo_dashboard.html', context)


# ============================================
# ADD COMPANY
# ============================================

@csrf_exempt
def tpo_add_company(request):
    if not request.session.get('tpo_logged_in'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        tpo_id = request.session.get('tpo_id')
        
        data = {
            'tpo_id': tpo_id,
            'company_name': request.POST.get('company_name'),
            'company_website': request.POST.get('company_website', ''),
            'industry': request.POST.get('industry', ''),
            'description': request.POST.get('description', ''),
            'logo_url': request.POST.get('logo_url', ''),
        }
        
        try:
            supabase.table('tpo_companies').insert(data).execute()
            messages.success(request, '✅ Company added successfully!')
            return redirect('tpo_dashboard')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    return render(request, 'tpo_add_company.html')


# ============================================
# ADD JOB / VACANCY
# ============================================

@csrf_exempt
def tpo_add_job(request):
    if not request.session.get('tpo_logged_in'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    tpo_id = request.session.get('tpo_id')
    companies = supabase.table('tpo_companies').select('*').eq('tpo_id', tpo_id).execute()
    
    if request.method == 'POST':
        data = {
            'company_id': request.POST.get('company_id'),
            'job_title': request.POST.get('job_title'),
            'job_description': request.POST.get('job_description'),
            'application_link': request.POST.get('application_link'),
            'location': request.POST.get('location', ''),
            'salary_range': request.POST.get('salary_range', ''),
            'experience_required': request.POST.get('experience_required', ''),
            'eligibility_criteria': request.POST.get('eligibility_criteria', ''),
            'application_deadline': request.POST.get('application_deadline') or None,
            'is_active': request.POST.get('is_active') == 'on',
        }
        
        try:
            supabase.table('tpo_jobs').insert(data).execute()
            messages.success(request, '✅ Job vacancy added successfully!')
            return redirect('tpo_dashboard')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    context = {
        'companies': companies.data if hasattr(companies, 'data') else [],
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_add_job.html', context)


# ============================================
# MANAGE COMPANIES
# ============================================

def tpo_manage_companies(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    tpo_id = request.session.get('tpo_id')
    companies = supabase.table('tpo_companies').select('*').eq('tpo_id', tpo_id).execute()
    
    context = {
        'companies': companies.data if hasattr(companies, 'data') else [],
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_manage_companies.html', context)


# ============================================
# MANAGE JOBS
# ============================================

def tpo_manage_jobs(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    jobs = supabase.table('tpo_jobs').select('*, company:company_id(company_name)').execute()
    
    context = {
        'jobs': jobs.data if hasattr(jobs, 'data') else [],
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_manage_jobs.html', context)


# ============================================
# EDIT JOB
# ============================================

@csrf_exempt
def tpo_edit_job(request, job_id):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    # Get job details
    job_response = supabase.table('tpo_jobs').select('*, company:company_id(company_name)').eq('id', job_id).execute()
    job = job_response.data[0] if job_response.data else None
    
    if not job:
        messages.error(request, '❌ Job not found!')
        return redirect('tpo_manage_jobs')
    
    # Get companies for dropdown
    tpo_id = request.session.get('tpo_id')
    companies = supabase.table('tpo_companies').select('*').eq('tpo_id', tpo_id).execute()
    
    if request.method == 'POST':
        data = {
            'company_id': request.POST.get('company_id'),
            'job_title': request.POST.get('job_title'),
            'job_description': request.POST.get('job_description'),
            'application_link': request.POST.get('application_link'),
            'location': request.POST.get('location', ''),
            'salary_range': request.POST.get('salary_range', ''),
            'experience_required': request.POST.get('experience_required', ''),
            'eligibility_criteria': request.POST.get('eligibility_criteria', ''),
            'application_deadline': request.POST.get('application_deadline') or None,
            'is_active': request.POST.get('is_active') == 'on',
        }
        
        try:
            supabase.table('tpo_jobs').update(data).eq('id', job_id).execute()
            messages.success(request, '✅ Job updated successfully!')
            return redirect('tpo_manage_jobs')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
    
    context = {
        'job': job,
        'companies': companies.data if hasattr(companies, 'data') else [],
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_edit_job.html', context)


# ============================================
# DELETE JOB
# ============================================

@csrf_exempt
def tpo_delete_job(request, job_id):
    if not request.session.get('tpo_logged_in'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        try:
            supabase.table('tpo_jobs').delete().eq('id', job_id).execute()
            messages.success(request, '✅ Job deleted successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
        
        return redirect('tpo_manage_jobs')
    
    return redirect('tpo_manage_jobs')


# ============================================
# VIEW APPLICATIONS
# ============================================

def tpo_applications(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    # Fetch applications with job and company details
    applications = supabase.table('tpo_placements')\
        .select('*, job:job_id(job_title, company:company_id(company_name))')\
        .execute()
    
    # Format data for template
    formatted_apps = []
    for app in applications.data if hasattr(applications, 'data') else []:
        formatted_apps.append({
            'id': app.get('id'),
            'student_name': app.get('student_name', ''),
            'student_email': app.get('student_email', ''),
            'student_phone': app.get('student_phone', ''),
            'resume_url': app.get('resume_url', ''),
            'status': app.get('status', 'applied'),
            'applied_at': app.get('applied_at', ''),
            'job_title': app.get('job', {}).get('job_title', '-') if app.get('job') else '-',
            'company_name': app.get('job', {}).get('company', {}).get('company_name', '-') if app.get('job') and app['job'].get('company') else '-',
        })
    
    context = {
        'applications': formatted_apps,
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_applications.html', context)


# ============================================
# UPDATE APPLICATION STATUS
# ============================================

@csrf_exempt
def tpo_update_application(request):
    if not request.session.get('tpo_logged_in'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        status = request.POST.get('status')
        
        try:
            supabase.table('tpo_placements').update({'status': status, 'updated_at': datetime.now().isoformat()}).eq('id', app_id).execute()
            messages.success(request, f'✅ Application status updated to {status}!')
        except Exception as e:
            messages.error(request, f'❌ Error: {e}')
        
        return redirect('tpo_applications')


# ============================================
# TPO PROFILE
# ============================================

def tpo_profile(request):
    if not request.session.get('tpo_logged_in'):
        return redirect('tpo_login')
    
    tpo_id = request.session.get('tpo_id')
    tpo = supabase.table('tpo').select('*').eq('tpo_id', tpo_id).execute()
    
    context = {
        'tpo': tpo.data[0] if tpo.data else {},
        'tpo_name': request.session.get('tpo_name', 'TPO'),
    }
    
    return render(request, 'tpo_profile.html', context)


# ============================================
# TPO LOGOUT
# ============================================

def tpo_logout(request):
    request.session.flush()
    messages.success(request, '✅ Logged out successfully!')
    return redirect('tpo_login')


# ============================================
# ISSUES DASHBOARD
# ============================================

def issues_dashboard(request):
    if not request.session.get('logged_in'):
        return redirect('admin_login')
    
    context = {
        'admin_name': request.session.get('username', 'Admin'),
        'total_students': 0,
        'total_faculty': 0,
        'total_tpo': 0,
        'total_hod': 0,
        'pending_count': 0,
        'in_progress_count': 0,
        'resolved_count': 0,
        'issues': [],
    }
    
    try:
        issues_res = supabase.table('infrastructure_issues').select('*').execute()
        issues = issues_res.data if hasattr(issues_res, 'data') else []
        context['issues'] = issues
        
        context['pending_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'pending')
        context['in_progress_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'in_progress')
        context['resolved_count'] = sum(1 for i in issues if i.get('status', '').lower() == 'resolved')
        
        # For sidebar counts
        student_res = supabase.table('student').select('*', count='exact').execute()
        context['total_students'] = len(student_res.data) if hasattr(student_res, 'data') else 0
        
        faculty_res = supabase.table('faculty').select('*', count='exact').execute()
        context['total_faculty'] = len(faculty_res.data) if hasattr(faculty_res, 'data') else 0
        
        tpo_res = supabase.table('tpo').select('*', count='exact').execute()
        context['total_tpo'] = len(tpo_res.data) if hasattr(tpo_res, 'data') else 0
        
        hod_res = supabase.table('hod').select('*', count='exact').execute()
        context['total_hod'] = len(hod_res.data) if hasattr(hod_res, 'data') else 0
        
    except Exception as e:
        print(f"Issues Dashboard Error: {e}")
    
    return render(request, 'issues_dashboard.html', context)