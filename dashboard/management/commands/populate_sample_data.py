from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Student, Skill
from dashboard.models import Internship, QuizQuestion, CodingQuestion, InterviewQuestion, RecommendedProject

class Command(BaseCommand):
    help = 'Populate the database with sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create skills
        skills_data = [
            'Python', 'JavaScript', 'React', 'Django', 'Node.js', 'HTML', 'CSS', 
            'Java', 'C++', 'SQL', 'MongoDB', 'PostgreSQL', 'Git', 'Docker',
            'AWS', 'Machine Learning', 'Data Analysis', 'UI/UX Design',
            'Project Management', 'Communication', 'Problem Solving'
        ]
        
        skills = []
        for skill_name in skills_data:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            skills.append(skill)
            if created:
                self.stdout.write(f'Created skill: {skill_name}')
        
        # Create sample internships
        internships_data = [
            {
                'title': 'Software Engineering Intern',
                'company': 'TechCorp Inc.',
                'description': 'Join our engineering team to work on cutting-edge web applications. You\'ll collaborate with senior developers, participate in code reviews, and contribute to our main product platform.',
                'location': 'San Francisco, CA',
                'stipend': 5000.00,
                'duration': '3 Months',
                'skills': ['Python', 'Django', 'JavaScript', 'React', 'SQL']
            },
            {
                'title': 'Data Science Intern',
                'company': 'DataFlow Analytics',
                'description': 'Work with our data science team to analyze large datasets and build machine learning models. Perfect opportunity to apply statistical knowledge in real-world scenarios.',
                'location': 'New York, NY',
                'stipend': 4500.00,
                'duration': '4 Months',
                'skills': ['Python', 'Machine Learning', 'Data Analysis', 'SQL']
            },
            {
                'title': 'Frontend Developer Intern',
                'company': 'DesignStudio Pro',
                'description': 'Create beautiful and responsive user interfaces for our client projects. You\'ll work closely with designers and backend developers to deliver exceptional user experiences.',
                'location': 'Austin, TX',
                'stipend': 4000.00,
                'duration': '3 Months',
                'skills': ['JavaScript', 'React', 'HTML', 'CSS', 'UI/UX Design']
            },
            {
                'title': 'Backend Developer Intern',
                'company': 'CloudTech Solutions',
                'description': 'Develop and maintain server-side applications and APIs. You\'ll learn about scalable architecture, database design, and cloud deployment.',
                'location': 'Seattle, WA',
                'stipend': 4800.00,
                'duration': '6 Months',
                'skills': ['Node.js', 'MongoDB', 'AWS', 'Docker', 'Git']
            },
            {
                'title': 'Mobile App Development Intern',
                'company': 'AppVentures',
                'description': 'Build cross-platform mobile applications using modern frameworks. Great opportunity to learn mobile development best practices.',
                'location': 'Los Angeles, CA',
                'stipend': 3800.00,
                'duration': '4 Months',
                'skills': ['JavaScript', 'React', 'HTML', 'CSS']
            },
            {
                'title': 'DevOps Engineering Intern',
                'company': 'InfraTech Systems',
                'description': 'Learn about CI/CD pipelines, containerization, and cloud infrastructure. You\'ll help automate deployment processes and monitor system performance.',
                'location': 'Remote',
                'stipend': 4200.00,
                'duration': '5 Months',
                'skills': ['Docker', 'AWS', 'Git', 'Python']
            }
        ]
        
        internships = []
        for internship_data in internships_data:
            internship, created = Internship.objects.get_or_create(
                title=internship_data['title'],
                company=internship_data['company'],
                defaults={
                    'description': internship_data['description'],
                    'location': internship_data['location'],
                    'stipend': internship_data['stipend'],
                    'duration': internship_data['duration']
                }
            )
            
            # Add required skills
            for skill_name in internship_data['skills']:
                skill = Skill.objects.get(name=skill_name)
                internship.required_skills.add(skill)
            
            internships.append(internship)
            if created:
                self.stdout.write(f'Created internship: {internship.title}')
        
        # Create sample quiz questions
        quiz_questions_data = [
            {
                'internship': internships[0],  # Software Engineering
                'question_text': 'What is the time complexity of binary search?',
                'options': {
                    'A': 'O(n)',
                    'B': 'O(log n)',
                    'C': 'O(n²)',
                    'D': 'O(1)'
                },
                'correct_answer_key': 'B'
            },
            {
                'internship': internships[1],  # Data Science
                'question_text': 'Which Python library is commonly used for data manipulation?',
                'options': {
                    'A': 'NumPy',
                    'B': 'Pandas',
                    'C': 'Matplotlib',
                    'D': 'All of the above'
                },
                'correct_answer_key': 'D'
            }
        ]
        
        for quiz_data in quiz_questions_data:
            quiz, created = QuizQuestion.objects.get_or_create(
                internship=quiz_data['internship'],
                question_text=quiz_data['question_text'],
                defaults={
                    'options': quiz_data['options'],
                    'correct_answer_key': quiz_data['correct_answer_key']
                }
            )
            if created:
                self.stdout.write(f'Created quiz question for {quiz.internship.title}')
        
        # Create sample coding questions
        coding_questions_data = [
            {
                'internship': internships[0],  # Software Engineering
                'title': 'Two Sum',
                'problem_statement': 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.',
                'test_cases': {
                    'input': '[2,7,11,15], target = 9',
                    'output': '[0,1]',
                    'explanation': 'Because nums[0] + nums[1] == 9, we return [0, 1].'
                }
            },
            {
                'internship': internships[3],  # Backend Developer
                'title': 'Valid Parentheses',
                'problem_statement': 'Given a string s containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
                'test_cases': {
                    'input': '"()"',
                    'output': 'true',
                    'explanation': 'The string contains valid parentheses.'
                }
            }
        ]
        
        for coding_data in coding_questions_data:
            coding, created = CodingQuestion.objects.get_or_create(
                internship=coding_data['internship'],
                title=coding_data['title'],
                defaults={
                    'problem_statement': coding_data['problem_statement'],
                    'test_cases': coding_data['test_cases']
                }
            )
            if created:
                self.stdout.write(f'Created coding question: {coding.title}')
        
        # Create sample interview questions
        interview_questions_data = [
            {
                'internship': internships[0],  # Software Engineering
                'question_text': 'Tell me about a challenging project you worked on.',
                'suggested_answer': 'Structure your answer using the STAR method (Situation, Task, Action, Result). Describe the project context, your specific role, the actions you took, and the positive outcome.'
            },
            {
                'internship': internships[1],  # Data Science
                'question_text': 'How would you handle missing data in a dataset?',
                'suggested_answer': 'Discuss various approaches: deletion (listwise/pairwise), imputation (mean/median/mode), or advanced techniques like multiple imputation. Mention the importance of understanding why data is missing.'
            }
        ]
        
        for interview_data in interview_questions_data:
            interview, created = InterviewQuestion.objects.get_or_create(
                internship=interview_data['internship'],
                question_text=interview_data['question_text'],
                defaults={
                    'suggested_answer': interview_data['suggested_answer']
                }
            )
            if created:
                self.stdout.write(f'Created interview question for {interview.internship.title}')
        
        # Create sample recommended projects
        project_data = [
            {
                'internship': internships[0],  # Software Engineering
                'title': 'Personal Portfolio Website',
                'description': 'Build a responsive portfolio website showcasing your projects, skills, and experience. Include contact forms and interactive elements.',
                'skills': ['HTML', 'CSS', 'JavaScript']
            },
            {
                'internship': internships[1],  # Data Science
                'title': 'Sales Data Analysis Dashboard',
                'description': 'Create an interactive dashboard that analyzes sales data, identifies trends, and provides actionable insights using Python and visualization libraries.',
                'skills': ['Python', 'Data Analysis']
            }
        ]
        
        for proj_data in project_data:
            project, created = RecommendedProject.objects.get_or_create(
                internship=proj_data['internship'],
                title=proj_data['title'],
                defaults={
                    'description': proj_data['description']
                }
            )
            
            # Add skills to gain
            for skill_name in proj_data['skills']:
                skill = Skill.objects.get(name=skill_name)
                project.skills_to_gain.add(skill)
            
            if created:
                self.stdout.write(f'Created recommended project: {project.title}')
        
        # Create a sample admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@lumo.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user (username: admin, password: admin123)'))
        
        # Create a sample student user
        if not User.objects.filter(username='student').exists():
            student_user = User.objects.create_user(
                username='student',
                email='student@example.com',
                password='student123',
                first_name='John',
                last_name='Doe'
            )
            
            # Create student profile
            student_profile = Student.objects.create(user=student_user)
            
            # Add some skills to the student
            sample_skills = ['Python', 'JavaScript', 'HTML', 'CSS', 'Git']
            for skill_name in sample_skills:
                skill = Skill.objects.get(name=skill_name)
                student_profile.skills.add(skill)
            
            self.stdout.write(self.style.SUCCESS('Created sample student user (username: student, password: student123)'))
        
        self.stdout.write(self.style.SUCCESS('Sample data creation completed successfully!'))
        self.stdout.write(self.style.WARNING('You can now login with:'))
        self.stdout.write('Admin: username=admin, password=admin123')
        self.stdout.write('Student: username=student, password=student123')
