from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # ✅ Index page pehle
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    
     # Student URLs
        path('student-login/', views.student_login, name='student_login'),
        path('student-verify-otp/', views.student_verify_otp, name='student_verify_otp'),
        path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
        path('student-logout/', views.student_logout, name='student_logout'),
        
         # TPO
    path('tpo-login/', views.tpo_login, name='tpo_login'),
    path('tpo-dashboard/', views.tpo_dashboard, name='tpo_dashboard'),
    path('tpo-logout/', views.tpo_logout, name='tpo_logout'),
]
