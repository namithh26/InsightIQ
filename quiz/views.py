import os
import re
import json
from django.shortcuts import render
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def home(request):
    return render(request, "quiz/home.html")

def generate_quiz(request):
    if request.method == "POST":
        topic = request.POST.get("topic", "").strip()
        if topic:
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": """You are a quiz generator. Return ONLY a JSON array, no extra text, in this exact format:
[
  {
    "question": "Question text here?",
    "options": ["A) Option1", "B) Option2", "C) Option3", "D) Option4"],
    "correct_answer": "A) Option1"
  }
]
The correct_answer must be the full option text including the letter prefix. Do not number the questions."""},
                        {"role": "user", "content": f"Generate 5 multiple-choice questions about {topic}."}
                    ],
                    model="llama-3.3-70b-versatile",
                )
                raw_questions = chat_completion.choices[0].message.content
                print(f"Raw API Response: {raw_questions}")
                questions = parse_quiz_response(raw_questions)
                request.session["questions"] = questions
                return render(request, "quiz/home.html", {"questions": questions})
            except Exception as e:
                print(f"Groq API Error: {e}")
                return render(request, "quiz/home.html", {"error": "Failed to generate quiz questions"})
    return render(request, "quiz/home.html", {"error": "Invalid request"})

def parse_quiz_response(raw_response):
    try:
        raw_response = raw_response.strip()
        start = raw_response.index('[')
        end = raw_response.rindex(']') + 1
        json_str = raw_response[start:end]
        questions = json.loads(json_str)
        for q in questions:
            q['question'] = re.sub(r'^\d+\.\s*', '', q['question'])
        return questions
    except Exception as e:
        print(f"Parsing error: {e}")
        return []

def submit_answers(request):
    if request.method == "POST":
        user_answers = {}
        for key, value in request.POST.items():
            if key.startswith("q"):
                user_answers[key] = value

        questions = request.session.get("questions", [])

        if not questions:
            return render(request, "quiz/home.html", {"error": "No quiz data found. Please generate a new quiz."})

        results = []
        for i, q in enumerate(questions):
            question_key = f"q{i + 1}"
            user_answer = user_answers.get(question_key, None)
            correct_answer = q["correct_answer"]
            is_correct = user_answer == correct_answer
            results.append({
                "question": q["question"],
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "user_answer": user_answer,
            })

        score = sum(1 for r in results if r['is_correct'])
        return render(request, 'quiz/home.html', {
            'results': results,
            'score': score,
            'total': len(results)
        })

    return render(request, "quiz/home.html")