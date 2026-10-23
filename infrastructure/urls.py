from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_issue, name='report_issue'),
    path('dashboard/', views.issues_dashboard, name='issues_dashboard'),
    path('update-status/<str:issue_id>/', views.update_issue_status, name='update_issue_status'),
    path('delete/<str:issue_id>/', views.delete_issue, name='delete_issue'),  # ✅ Admin delete
]