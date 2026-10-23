import uuid
from django.db import models
from django.utils import timezone

class TPO(models.Model):
    tpo_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=15)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} - {self.full_name}"

    class Meta:
        db_table = 'tpo'
        ordering = ['-created_at']
        
        
# ============================================
# TPO COMPANIES
# ============================================

class TPOCompany(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tpo_id = models.CharField(max_length=50)
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    class Meta:
        db_table = 'tpo_companies'
        ordering = ['-created_at']


# ============================================
# TPO JOBS / VACANCIES
# ============================================

class TPOJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(TPOCompany, on_delete=models.CASCADE, related_name='jobs')
    job_title = models.CharField(max_length=200)
    job_description = models.TextField()
    application_link = models.URLField(max_length=500)
    location = models.CharField(max_length=100, blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    experience_required = models.CharField(max_length=50, blank=True, null=True)
    eligibility_criteria = models.TextField(blank=True, null=True)
    application_deadline = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company.company_name} - {self.job_title}"

    class Meta:
        db_table = 'tpo_jobs'
        ordering = ['-created_at']


# ============================================
# TPO PLACEMENTS (Student Applications)
# ============================================

class TPPlacement(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(TPOJob, on_delete=models.CASCADE, related_name='applications')
    student_id = models.CharField(max_length=50)
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField(max_length=100)
    student_phone = models.CharField(max_length=15)
    resume_url = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tpo_placements'
        ordering = ['-applied_at']
        unique_together = ('job', 'student_id')