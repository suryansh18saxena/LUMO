import json
import pdfplumber
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Student, Skill
from .models import Internship, Application, QuizQuestion, InterviewQuestion, RecommendedProject
from .ai import get_ai_generated_questions

# --- Page Rendering Views ---

@login_required
def dashboard(request):
    """
    Displays the main dashboard page with a list of all available internships.
    """
    # Get or create student profile
    student_profile, created = Student.objects.get_or_create(user=request.user)
    
    # Fetch all internship objects, ordered by the most recently posted.
    internships = Internship.objects.all().order_by('-posted_date')
    
    # Get recommended internships based on student skills
    recommended_internships = get_recommended_internships(student_profile)
    
    # Get all skills for filter
    all_skills = Skill.objects.all()
    
    context = {
        'internships': internships,
        'recommended_internships': recommended_internships,
        'all_skills': all_skills,
        'student': student_profile
    }
    return render(request, 'dashboard/index.html', context)

def get_recommended_internships(student):
    """
    Get internships that match student's skills with improved matching
    """
    if not student.skills.exists():
        return []
    
    student_skills = student.skills.all()
    recommended = []
    
    for internship in Internship.objects.all():
        required_skills = internship.required_skills.all()
        if not required_skills.exists():
            continue
            
        # Improved skill matching (case-insensitive and partial matching)
        matching_skills = []
        for req_skill in required_skills:
            for student_skill in student_skills:
                if (req_skill.name.lower() == student_skill.name.lower() or 
                    req_skill.name.lower() in student_skill.name.lower() or
                    student_skill.name.lower() in req_skill.name.lower()):
                    matching_skills.append(req_skill)
                    break
        
        if matching_skills:
            match_percentage = (len(matching_skills) / required_skills.count()) * 100
            if match_percentage >= 25:  # At least 25% match
                recommended.append({
                    'internship': internship,
                    'matching_skills': matching_skills,
                    'match_percentage': round(match_percentage, 1)
                })
    
    # Sort by match percentage
    recommended.sort(key=lambda x: x['match_percentage'], reverse=True)
    return recommended



# --- API Views ---

def parse_resume_with_pdfplumber(resume_file):
    """
    Parse resume PDF using pdfplumber to extract text and structure it.
    """
    try:
        with pdfplumber.open(resume_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        # Basic parsing logic - in production, you'd use more sophisticated NLP
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Extract basic information
        parsed_data = {
            "contact_info": extract_contact_info(lines),
            "summary": extract_summary(lines),
            "experience": extract_experience(lines),
            "education": extract_education(lines),
            "skills": extract_skills(lines),
            "projects": extract_projects(lines),
            "raw_text": text
        }
        
        return parsed_data
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None

def extract_contact_info(lines):
    """Extract contact information from resume lines"""
    contact_info = {"name": "", "email": "", "phone": "", "linkedin": ""}
    
    for i, line in enumerate(lines[:15]):  # Check first 15 lines
        line_lower = line.lower().strip()
        line_clean = line.strip()
        
        # Email detection
        if "@" in line_clean and "." in line_clean and not contact_info["email"]:
            import re
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line_clean)
            if email_match:
                contact_info["email"] = email_match.group()
        
        # LinkedIn detection
        elif "linkedin" in line_lower and not contact_info["linkedin"]:
            contact_info["linkedin"] = line_clean
        
        # Phone detection
        elif not contact_info["phone"]:
            import re
            phone_patterns = [
                r'\+?1?[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',
                r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}',
                r'\d{3}[-\s]?\d{3}[-\s]?\d{4}'
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, line_clean)
                if phone_match:
                    contact_info["phone"] = phone_match.group()
                    break
        
        # Name detection - look for lines that are likely names
        if not contact_info["name"] and i < 5:
            # Skip lines that are clearly not names
            skip_keywords = ['resume', 'cv', 'curriculum', 'vitae', 'email', 'phone', 'address', 'linkedin']
            if (len(line_clean.split()) <= 4 and 
                not any(keyword in line_lower for keyword in skip_keywords) and
                not any(char.isdigit() for char in line_clean) and
                not "@" in line_clean and
                len(line_clean) > 3):
                contact_info["name"] = line_clean
    
    return contact_info

def extract_summary(lines):
    """Extract summary/objective from resume"""
    summary_keywords = ["summary", "objective", "profile", "about"]
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in summary_keywords):
            # Return next few lines as summary
            return " ".join(lines[i+1:i+4])
    return ""

def extract_experience(lines):
    """Extract work experience from resume with better parsing"""
    experience = []
    exp_keywords = ["experience", "work", "employment", "career", "professional", "internship"]
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in exp_keywords) and len(line.strip()) < 50:
            # Look for experience entries in the following lines
            j = i + 1
            current_exp = None
            
            while j < len(lines) and j < i + 15:
                current_line = lines[j].strip()
                if not current_line:
                    j += 1
                    continue
                
                # Stop if we hit another major section
                if any(section in current_line.lower() for section in ["education", "skills", "projects", "certifications"]):
                    break
                
                # Look for job titles (usually shorter lines, may contain dates)
                if len(current_line) < 100 and (any(char.isdigit() for char in current_line) or 
                                               any(word in current_line.lower() for word in ["intern", "developer", "engineer", "analyst", "manager"])):
                    if current_exp:
                        experience.append(current_exp)
                    
                    current_exp = {
                        "title": current_line,
                        "company": "",
                        "description": ""
                    }
                    
                    # Look for company name in next line
                    if j + 1 < len(lines) and lines[j + 1].strip():
                        next_line = lines[j + 1].strip()
                        if len(next_line) < 80 and not next_line.startswith("•"):
                            current_exp["company"] = next_line
                            j += 1
                
                # Collect description lines
                elif current_exp and (current_line.startswith("•") or current_line.startswith("-") or len(current_line) > 50):
                    if current_exp["description"]:
                        current_exp["description"] += " " + current_line
                    else:
                        current_exp["description"] = current_line
                
                j += 1
            
            if current_exp:
                experience.append(current_exp)
            break
    
    return experience[:5]  # Limit to 5 experiences

def extract_education(lines):
    """Extract education information from resume with better parsing"""
    education = []
    edu_keywords = ["education", "degree", "university", "college", "school", "academic"]
    
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in edu_keywords) and len(line.strip()) < 50:
            # Look for education entries
            j = i + 1
            current_edu = None
            
            while j < len(lines) and j < i + 10:
                current_line = lines[j].strip()
                if not current_line:
                    j += 1
                    continue
                
                # Stop if we hit another section
                if any(section in current_line.lower() for section in ["experience", "skills", "projects"]):
                    break
                
                # Look for degree or institution
                if len(current_line) < 100:
                    if any(degree in current_line.lower() for degree in ["bachelor", "master", "phd", "degree", "university", "college"]):
                        if current_edu:
                            education.append(current_edu)
                        
                        current_edu = {
                            "degree": current_line,
                            "institution": "",
                            "dates": ""
                        }
                        
                        # Look for institution in next line
                        if j + 1 < len(lines) and lines[j + 1].strip():
                            next_line = lines[j + 1].strip()
                            if len(next_line) < 80:
                                current_edu["institution"] = next_line
                                j += 1
                    
                    # Look for dates
                    elif current_edu and any(char.isdigit() for char in current_line):
                        import re
                        if re.search(r'\d{4}', current_line):
                            current_edu["dates"] = current_line
                
                j += 1
            
            if current_edu:
                education.append(current_edu)
            break
    
    return education[:3]  # Limit to 3 education entries

def extract_skills(lines):
    """Extract skills from resume with improved accuracy"""
    skills = []
    skill_keywords = ["skills", "technologies", "tools", "programming", "technical", "software", "languages"]
    
    # Common technical skills to look for
    common_skills = {
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 'django', 'flask',
        'html', 'css', 'sql', 'mongodb', 'postgresql', 'mysql', 'git', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'machine learning', 'data analysis', 'pandas', 'numpy', 'tensorflow',
        'pytorch', 'scikit-learn', 'r', 'matlab', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'swift', 'kotlin', 'flutter', 'react native', 'bootstrap', 'tailwind', 'sass', 'less',
        'webpack', 'babel', 'typescript', 'graphql', 'rest api', 'microservices', 'agile', 'scrum'
    }
    
    # First, look for dedicated skills sections
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in skill_keywords):
            # Look for skills in next several lines
            for j in range(i+1, min(i+8, len(lines))):
                if lines[j] and not lines[j].lower().startswith(("experience", "education", "projects")):
                    # Split by various delimiters
                    delimiters = [',', '•', '·', '|', ';', '/', '\n', '\t']
                    line_text = lines[j]
                    for delimiter in delimiters:
                        line_text = line_text.replace(delimiter, '|')
                    
                    line_skills = [s.strip() for s in line_text.split('|') if s.strip()]
                    
                    for skill in line_skills:
                        skill_clean = skill.lower().strip()
                        if len(skill_clean) > 1 and len(skill_clean) < 30:
                            skills.append(skill.strip())
                    break
    
    # Also scan entire document for common technical skills
    full_text = ' '.join(lines).lower()
    for skill in common_skills:
        if skill in full_text and skill.title() not in skills:
            skills.append(skill.title())
    
    # Clean and deduplicate skills
    cleaned_skills = []
    seen = set()
    for skill in skills:
        skill_clean = skill.strip().title()
        if skill_clean and skill_clean.lower() not in seen and len(skill_clean) > 1:
            cleaned_skills.append(skill_clean)
            seen.add(skill_clean.lower())
    
    return cleaned_skills[:20]  # Limit to 20 skills

def extract_projects(lines):
    """Extract projects from resume"""
    projects = []
    proj_keywords = ["projects", "portfolio", "work"]
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in proj_keywords):
            for j in range(i+1, min(i+8, len(lines))):
                if lines[j] and not lines[j].lower().startswith(("experience", "education", "skills")):
                    projects.append({
                        "title": lines[j],
                        "description": " ".join(lines[j+1:j+3]) if j+1 < len(lines) else ""
                    })
                    break
    
    return projects

@csrf_exempt
@login_required
def upload_resume_api_view(request):
    """
    API view to handle the resume file upload, parse it using an AI model,
    and save the structured JSON data to the student's profile.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

    if 'resume' not in request.FILES:
        return JsonResponse({'error': 'No resume file provided'}, status=400)

    try:
        # Get or create student profile
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            student = Student.objects.create(user=request.user)
        
        resume_file = request.FILES['resume']

        # Delete old resume file if exists
        if student.resume:
            try:
                student.resume.delete()
            except:
                pass

        # 1. Save the original resume file to the 'resume' field
        student.resume = resume_file
        student.save()  # Save first to get the file path
        
        # 2. Call the function to parse the resume
        parsed_data = parse_resume_with_pdfplumber(student.resume.path)
        
        if not parsed_data:
            return JsonResponse({'error': 'Failed to parse resume. Please ensure it is a valid PDF.'}, status=400)

        # 3. Save the structured JSON to the 'resume_json_data' field
        student.resume_json_data = parsed_data
        
        # Clear existing skills and add new ones
        student.skills.clear()
        
        # Auto-create skills from parsed resume
        if 'skills' in parsed_data and parsed_data['skills']:
            for skill_name in parsed_data['skills']:
                if skill_name and len(skill_name.strip()) > 1:
                    skill, created = Skill.objects.get_or_create(
                        name__iexact=skill_name.strip(),
                        defaults={'name': skill_name.strip().title()}
                    )
                    student.skills.add(skill)
        
        student.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Resume uploaded and parsed successfully!',
            'data': parsed_data,
            'skills_count': student.skills.count()
        })

    except Exception as e:
        print(f"An error occurred in upload_resume_api_view: {e}")
        return JsonResponse({'error': f'An internal server error occurred: {str(e)}'}, status=500)

@login_required
def resume_upload(request):
    """
    Resume upload page view
    """
    student_profile, created = Student.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/resume_upload.html', {'student': student_profile})

@login_required
def resume_preview(request):
    """
    Preview parsed resume data
    """
    student_profile, created = Student.objects.get_or_create(user=request.user)
    return render(request, 'dashboard/resume_preview.html', {'student': student_profile})

@login_required
def my_applications(request):
    """
    Display student's applications
    """
    student_profile, created = Student.objects.get_or_create(user=request.user)
    applications = Application.objects.filter(student=student_profile).order_by('-applied_date')
    
    return render(request, 'dashboard/my_applications.html', {
        'applications': applications,
        'student': student_profile
    })

@login_required
def recommended_internships(request):
    """
    Display recommended internships based on student skills
    """
    student_profile, created = Student.objects.get_or_create(user=request.user)
    recommended = get_recommended_internships(student_profile)
    
    return render(request, 'dashboard/recommended_internships.html', {
        'internships': recommended,
        'student': student_profile
    })

# @login_required
# def training(request):
#     """
#     Training roadmap page with internship-specific quizzes, interview questions, and projects
#     """
#     student_profile, created = Student.objects.get_or_create(user=request.user)
    
#     # Get recommended internships for the student
#     recommended_internships = get_recommended_internships(student_profile)
    
#     # Get training data for recommended internships
#     training_data = []
#     for rec in recommended_internships[:3]:  # Limit to top 3 recommendations
#         internship = rec['internship']
#         training_data.append({
#             'internship': internship,
#             'match_percentage': rec['match_percentage'],
#             'quiz_questions': list(internship.quiz_questions.all()),
#             'interview_questions': list(internship.interview_questions.all()),
#             'recommended_projects': list(internship.recommended_projects.all())
#         })
    
#     return render(request, 'dashboard/training.html', {
#         'student': student_profile,
#         'training_data': training_data,
#         'has_recommendations': len(training_data) > 0
#     })

# ======================================Preparation======================================

@login_required
def practice_quiz(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)
    quiz_questions = internship.quiz_questions.all()
    context = {
        'internship': internship,
        'quiz_questions': quiz_questions
    }
    return render(request, 'dashboard/practice_quiz.html', context)

@login_required
def coding_challenges(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)
    coding_questions = internship.coding_questions.all()
    context = {
        'internship': internship,
        'coding_questions': coding_questions
    }
    return render(request, 'dashboard/coding_challenges.html', context)

@login_required
def interview_questions(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)
    interview_questions = internship.interview_questions.all()
    context = {
        'internship': internship,
        'interview_questions': interview_questions
    }
    return render(request, 'dashboard/interview_questions.html', context)


@login_required
def internship_detail(request, internship_id):
    """
    Display detailed view of a specific internship
    """
    internship = get_object_or_404(Internship, id=internship_id)
    student_profile, created = Student.objects.get_or_create(user=request.user)
    
    # Check if student has already applied
    has_applied = Application.objects.filter(student=student_profile, internship=internship).exists()
    
    # Get matching skills
    student_skills = student_profile.skills.all()
    matching_skills = []
    required_skills = internship.required_skills.all()
    
    for req_skill in required_skills:
        for student_skill in student_skills:
            if (req_skill.name.lower() == student_skill.name.lower() or 
                req_skill.name.lower() in student_skill.name.lower() or
                student_skill.name.lower() in req_skill.name.lower()):
                matching_skills.append(req_skill)
                break
    
    match_percentage = 0
    if required_skills.exists():
         match_percentage = (len(matching_skills) / required_skills.count()) * 100

    context = {
        'internship': internship,
        'student': student_profile,
        'has_applied': has_applied,
        'matching_skills': matching_skills,
        'match_percentage': round(match_percentage, 1),
        'required_skills': required_skills,
    }
    
    return render(request, 'dashboard/internship_detail.html', context)

@login_required
def apply_internship(request, internship_id):
    """
    Apply for an internship
    """
    internship = get_object_or_404(Internship, id=internship_id)
    student_profile, created = Student.objects.get_or_create(user=request.user)
    


    # Check if already applied
    if Application.objects.filter(student=student_profile, internship=internship).exists():
        messages.warning(request, f'You have already applied for {internship.title} at {internship.company}!')
    else:
        # Create application
        Application.objects.create(student=student_profile, internship=internship)
        messages.success(request, f'Successfully applied for {internship.title} at {internship.company}!')
    
    return redirect('internship_detail', internship_id=internship_id)


@login_required
def mock_interview(request):
    """
    Conduct a mock interview for the student
    """
    student_profile, created = Student.objects.get_or_create(user=request.user)
    # Logic for conducting a mock interview goes here
    return render(request, 'dashboard/mock_interview.html', {'student': student_profile})