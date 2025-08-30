from django.contrib import admin
from .models import Internship, Application, QuizQuestion, CodingQuestion, InterviewQuestion

# Register your models here.

admin.site.register(Internship)
admin.site.register(Application)
admin.site.register(QuizQuestion)
admin.site.register(CodingQuestion)
admin.site.register(InterviewQuestion)
