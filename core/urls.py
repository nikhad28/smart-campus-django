from django.urls import path
from . import views
# core/views.py - Add this import at the top with other imports
from .utils.career_recommender import recommender, get_career_recommendation
urlpatterns = [
    # ============================================
    # INDEX / HOME
    # ============================================
    path('', views.index, name='index'),

    # ============================================
    # ADMIN URLs
    # ============================================
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-students/', views.admin_students, name='admin_students'),
    path('admin-faculty/', views.admin_faculty, name='admin_faculty'),
    path('admin-tpo/', views.admin_tpo, name='admin_tpo'),
    path('admin-hod/', views.admin_hod, name='admin_hod'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-reports/', views.admin_reports, name='admin_reports'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('student-skill-profile/<int:student_id>/', views.student_skill_profile, name='student_skill_profile'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    # Admin Add URLs (Modal forms submit yahan karenge)
path('admin-add-student/', views.admin_add_student, name='admin_add_student'),
path('admin-add-faculty/', views.admin_add_faculty, name='admin_add_faculty'),
path('admin-add-tpo/', views.admin_add_tpo, name='admin_add_tpo'),
path('admin-add-hod/', views.admin_add_hod, name='admin_add_hod'),
    
    # Student URLs
path('student-login/', views.student_login, name='student_login'),
path('student-verify-otp/', views.student_verify_otp, name='student_verify_otp'),
path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
path('student-apply/<str:job_id>/', views.student_apply_job, name='student_apply_job'),
path('student-logout/', views.student_logout, name='student_logout'),

# ✅ Student Pages URLs
path('student-my-courses/', views.student_my_courses, name='student_my_courses'),
path('student-results/', views.student_results, name='student_results'),
path('student-profile/', views.student_profile, name='student_profile'),
path('student-skill-profile/', views.student_skill_profile, name='student_skill_profile'),
path('career-recommendation/', views.career_recommendation, name='career_recommendation'),
path('get-career-prediction/', views.get_career_prediction_ajax, name='get_career_prediction_ajax'),


    # ============================================
    # TPO URLs
    # ============================================
    path('tpo-login/', views.tpo_login, name='tpo_login'),
    path('tpo-dashboard/', views.tpo_dashboard, name='tpo_dashboard'),
    path('tpo-add-company/', views.tpo_add_company, name='tpo_add_company'),
    path('tpo-add-job/', views.tpo_add_job, name='tpo_add_job'),
    path('tpo-manage-companies/', views.tpo_manage_companies, name='tpo_manage_companies'),
    path('tpo-manage-jobs/', views.tpo_manage_jobs, name='tpo_manage_jobs'),
    path('tpo-edit-job/<str:job_id>/', views.tpo_edit_job, name='tpo_edit_job'),
    path('tpo-delete-job/<str:job_id>/', views.tpo_delete_job, name='tpo_delete_job'),
    path('tpo-applications/', views.tpo_applications, name='tpo_applications'),
    path('tpo-update-application/', views.tpo_update_application, name='tpo_update_application'),
    path('tpo-profile/', views.tpo_profile, name='tpo_profile'),
    path('tpo-logout/', views.tpo_logout, name='tpo_logout'),
    
    # ============================================
    # ISSUES URL
    # ============================================
    path('issues-dashboard/', views.issues_dashboard, name='issues_dashboard'),
    # Faculty URLs
path('admin-update-faculty-status/<int:faculty_id>/', views.admin_update_faculty_status, name='admin_update_faculty_status'),
path('admin-update-faculty/<int:faculty_id>/', views.admin_update_faculty, name='admin_update_faculty'),
path('admin-delete-faculty/<int:faculty_id>/', views.admin_delete_faculty, name='admin_delete_faculty'),
]