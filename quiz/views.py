import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from httpcore import request
from dotenv import load_dotenv
from groq import Groq

# Load API key from .env file
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def home(request):
    """Render the home page."""
    return render(request, "quiz/home.html")

def generate_quiz(request):
    """Generate quiz questions using Groq API."""
    if request.method == "POST":
        topic = request.POST.get("topic", "").strip()
        if topic:
            print(f"Received Topic: {topic}")  # Debugging
            try:
                # Sending request to Groq API
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
The correct_answer must be the full option text including the letter prefix."""},
                    ],
                    model="llama-3.3-70b-versatile",
                )
                raw_questions = chat_completion.choices[0].message.content
                print(f"Raw API Response: {raw_questions}")  # Debugging

                # Parse the raw response into a structured format
                questions = parse_quiz_response(raw_questions)

                # Store questions in session
                request.session["questions"] = questions
                print(f"Session Questions: {request.session['questions']}")  # Debugging

                # Pass the parsed questions to the template
                return render(request, "quiz/home.html", {"questions": questions})
            except Exception as e:
                print(f"Groq API Error: {e}")
                return render(request, "quiz/home.html", {"error": "Failed to generate quiz questions"})
    return render(request, "quiz/home.html", {"error": "Invalid request"})

import re

import json


def parse_quiz_response(raw_response):
    try:
        raw_response = raw_response.strip()
        start = raw_response.index('[')
        end = raw_response.rindex(']') + 1
        json_str = raw_response[start:end]
        questions = json.loads(json_str)
        # Strip leading numbers like "1. " from question text
        for q in questions:
            q['question'] = re.sub(r'^\d+\.\s*', '', q['question'])
        return questions
    except Exception as e:
        print(f"Parsing error: {e}")
        return []

def submit_answers(request):
    """Process user answers and check correctness."""
    if request.method == "POST":
        # Retrieve the submitted answers from the form
        user_answers = {}
        for key, value in request.POST.items():
            if key.startswith("q"):  # Question keys start with "q"
                user_answers[key] = value

        # Retrieve the generated questions and correct answers (stored in session)
        questions = request.session.get("questions", [])
        print(f"Session Questions in Submit Answers: {questions}")  # Debugging

        if not questions:
            # If no questions are found in the session, return an error
            return render(request, "quiz/home.html", {"error": "No quiz data found. Please generate a new quiz."})

        results = []

        for q in questions:
            question_key = f"q{questions.index(q) + 1}"  # e.g., "q1", "q2", etc.
            user_answer = user_answers.get(question_key, None)
            correct_answer = q["correct_answer"]  # Correct answer stored in the question data

            # Check if the user's answer is correct
            is_correct = user_answer == correct_answer
            results.append({
                "question": q["question"],
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "user_answer": user_answer,  # Include the user's answer in the results
            })
        score = sum(1 for r in results if r['is_correct'])

        return render(request, 'quiz/home.html', {
    'results': results,
    'score': score,
    'total': len(results)
})
