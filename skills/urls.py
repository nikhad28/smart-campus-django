from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.skills_dashboard, name='skills_dashboard'),
     path('student/<int:student_id>/', views.student_skill_profile, name='student_skill_profile'),
    path('api/predict/<int:student_id>/', views.predict_api, name='predict_api'),
]