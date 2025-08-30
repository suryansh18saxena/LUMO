from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("resume/upload/", views.resume_upload, name="resume_upload"),
    path("resume/preview/", views.resume_preview, name="resume_preview"),
    path("resume/upload-api/", views.upload_resume_api_view, name="upload_resume_api"),
    path("internship/<int:internship_id>/", views.internship_detail, name="internship_detail"),
    path("internship/<int:internship_id>/apply/", views.apply_internship, name="apply_internship"),
    path("applications/", views.my_applications, name="my_applications"),
    path("recommended/", views.recommended_internships, name="recommended_internships"),
    path("training/", views.training, name="training"),
]
