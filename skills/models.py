from django.db import models

class SkillDomain(models.Model):
    domain_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.domain_name

class SkillSubject(models.Model):
    subject_code = models.CharField(max_length=20, unique=True)
    subject_name = models.CharField(max_length=100)
    domain = models.ForeignKey(SkillDomain, on_delete=models.CASCADE, related_name='subjects')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.subject_name

class SkillStudentMarks(models.Model):
    student_id = models.IntegerField()
    subject = models.ForeignKey(SkillSubject, on_delete=models.CASCADE)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student_id', 'subject', 'semester']

class SkillDomainPrediction(models.Model):
    student_id = models.IntegerField()
    primary_domain = models.ForeignKey(SkillDomain, on_delete=models.CASCADE)
    domain_scores = models.JSONField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    predicted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

class SkillStudentProfile(models.Model):
    student_id = models.IntegerField(unique=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    recommended_domain = models.ForeignKey(SkillDomain, on_delete=models.SET_NULL, null=True)
    all_domain_ranking = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)