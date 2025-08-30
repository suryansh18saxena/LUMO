from django.db import models
from accounts.models import Student, Skill

# Create your models here.

class Internship(models.Model):
    """
    Represents an internship listing.
    """
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=150)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100, help_text="e.g., '3 Months', '6 Weeks'")
    required_skills = models.ManyToManyField(Skill, related_name='internships')
    posted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

# ... (Other models like Application, QuizQuestion, etc., remain the same) ...
class Application(models.Model):
    STATUS_CHOICES = [
        ('Applied', 'Applied'),
        ('In Review', 'In Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
        ('Hired', 'Hired'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Applied')
    applied_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('student', 'internship')
    def __str__(self):
        return f"{self.student.user.username}'s application for {self.internship.title}"

class QuizQuestion(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='quiz_questions')
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer_key = models.CharField(max_length=10, help_text="e.g., 'A', 'B'")
    def __str__(self):
        return f"Quiz Question for {self.internship.title}"

class CodingQuestion(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='coding_questions')
    title = models.CharField(max_length=255)
    problem_statement = models.TextField()
    test_cases = models.JSONField()
    def __str__(self):
        return f"Coding Question: {self.title} for {self.internship.title}"

class InterviewQuestion(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='interview_questions')
    question_text = models.TextField()
    suggested_answer = models.TextField(blank=True, null=True, help_text="An ideal answer or key points to cover.")
    def __str__(self):
        return f"Interview Question for {self.internship.title}"

class RecommendedProject(models.Model):
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='recommended_projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    skills_to_gain = models.ManyToManyField(Skill, blank=True)
    def __str__(self):
        return f"Project: {self.title} for {self.internship.title}"

