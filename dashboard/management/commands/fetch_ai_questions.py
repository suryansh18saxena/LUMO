from django.core.management.base import BaseCommand
from dashboard.models import Internship, QuizQuestion, CodingQuestion, InterviewQuestion
from dashboard.ai import get_ai_generated_questions

class Command(BaseCommand):
    help = 'Fetch AI-generated questions for a specific internship and store them in the database'

    def add_arguments(self, parser):
        parser.add_argument('internship_id', type=int, help='The ID of the internship to fetch questions for')

    def handle(self, *args, **options):
        internship_id = options['internship_id']
        try:
            internship = Internship.objects.get(id=internship_id)
        except Internship.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Internship with ID "{internship_id}" does not exist.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Fetching questions for "{internship.title}"...'))

        # Call your AI function
        skills = internship.required_skills.all()
        generated_data = get_ai_generated_questions(internship.company, skills)

        if not generated_data:
            self.stdout.write(self.style.ERROR('Failed to fetch data from the API.'))
            return

        # --- Save Quiz Questions ---
        for q_data in generated_data.get('quiz', []):
            QuizQuestion.objects.get_or_create(
                internship=internship,
                question_text=q_data['question_text'],
                defaults={
                    'options': q_data['options'],
                    'correct_answer_key': q_data['correct_answer_key']
                }
            )

        # --- Save Coding Challenges ---
        for c_data in generated_data.get('coding', []):
            CodingQuestion.objects.get_or_create(
                internship=internship,
                title=c_data['title'],
                defaults={
                    'problem_statement': c_data['problem_statement'],
                    'test_cases': c_data.get('test_cases', {})
                }
            )

        # --- Save Interview Questions ---
        for i_data in generated_data.get('interview', []):
            InterviewQuestion.objects.get_or_create(
                internship=internship,
                question_text=i_data['question_text'],
                defaults={'suggested_answer': i_data['suggested_answer']}
            )

        self.stdout.write(self.style.SUCCESS('Successfully saved all questions to the database!'))
        