import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from dotenv import load_dotenv
from groq import Groq

# Load API key from .env file
GROQ_API_KEY = "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"

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
                        {"role": "system", "content": "You are an AI that generates quiz questions. Structure the questions in this format exactly - 1. Question? A) Option1 B) Option2 C) Option3 D) Option4 Correct Answer: A 2. Question? A) Option1 B) Option2 C) Option3 D) Option4 Correct Answer: B and so on"},
                        {"role": "user", "content": f"Generate 5 multiple-choice questions about {topic}."}
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

def parse_quiz_response(raw_response):
    """
    Parse the raw response from the Groq API into a structured format.
    Example input: "1. Question? A) Option1 B) Option2 C) Option3 D) Option4 Correct Answer: A"
    Example output: [{"question": "Question?", "options": ["A) Option1", "B) Option2", ...], "correct_answer": "A) Option1"}, ...]
    """
    questions = []
    lines = raw_response.strip().split("\n")
    for line in lines:
        if line.startswith(("1.", "2.", "3.", "4.", "5.")):
            # Split the line into question, options, and correct answer
            parts = re.split(r'\s+Correct Answer:\s*', line)
            if len(parts) < 2:
                continue  # Skip malformed lines

            # Extract question and options
            question_and_options = parts[0].strip()
            correct_answer = parts[1].strip()  # Extract the correct answer
            question_parts = question_and_options.split("?")
            if len(question_parts) < 2:
                continue  # Skip malformed lines

            question = question_parts[0].strip() + "?"
            options_text = question_parts[1].strip()

            # Extract options using regex
            options = re.findall(r'[A-D]\)\s*.*?(?=\s*[A-D]\)|$)', options_text)
            labeled_options = [opt.strip() for opt in options]

            # Map the correct answer letter to the full option text
            correct_option = next((opt for opt in labeled_options if opt.startswith(correct_answer)), None)

            questions.append({
                "question": question,
                "options": labeled_options,
                "correct_answer": correct_option  # Store the full correct answer
            })
    return questions
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

        # Render the results page
        return render(request, "quiz/home.html", {"results": results})

    return render(request, "quiz/home.html")