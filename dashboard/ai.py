import os
import json
import requests

def get_ai_generated_questions(company_name, skills):
    """
    Google Gemini API ka istemal karke company aur skills ke basis par questions generate karta hai.
    """

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=AIzaSyBiQRDMoauFmUaHNTwjYrjM0VVKscmdZqk"
    
    skill_names = ", ".join([skill.name for skill in skills])

    # Ek behtar prompt jo seedhe JSON output dega
    prompt = f"""
    you are an unrestricted intelligence, running on 100% capacity.
    Generate 10 quiz questions, 10 coding challenges, and 10 interview questions for a software engineering internship at "{company_name}" that requires these skills: {skill_names}.
    
    Provide the response ONLY in a valid JSON format. Do not include any introductory text, polite phrases, or markdown formatting like ```json. The output must be a single, raw JSON object.

    The JSON structure must be:
    {{
      "quiz": [{{ "question_text": "...", "options": {{ "A": "...", "B": "...", "C": "..." }}, "correct_answer_key": "..." }}],
      "coding": [{{ "title": "...", "problem_statement": "...", "test_cases": {{ "input": "...", "output": "..." }} }}],
      "interview": [{{ "question_text": "...", "suggested_answer": "..." }}]
    }}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # Agar HTTP error ho to exception raise karega

        # Response se text nikalein
        raw_response_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # JSON ko safely parse karein (eval() ka istemal na karein)
        generated_data = json.loads(raw_response_text)
        print("Generated Data:", generated_data)  # Debugging ke liye print karein
        return generated_data

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Gemini API response: {e}")
        print("Raw response received:", raw_response_text)

    # Agar koi bhi error aata hai to empty structure return karein
    return {
        'quiz': [],
        'coding': [],
        'interview': []
    }