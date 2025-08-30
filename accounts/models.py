from django.db import models
from django.contrib.auth.models import User

# --- Core Models ---

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    resume = models.FileField(upload_to='resumes/', blank=True, null=True, help_text="The original resume file uploaded by the student.")
    
    resume_json_data = models.JSONField(null=True, blank=True, help_text="Extracted and structured data from the resume.")
    
    skills = models.ManyToManyField(Skill, blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
