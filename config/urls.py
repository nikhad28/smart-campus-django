from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Django default admin
    path('', include('core.urls')),   # Custom index, login, dashboard
]