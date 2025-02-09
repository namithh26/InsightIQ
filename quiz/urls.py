from django.urls import path
from .views import home, generate_quiz, submit_answers

urlpatterns = [
    path("", home, name="home"),
    path("generate/", generate_quiz, name="generate_quiz"),
    path("submit/", submit_answers, name="submit_answers"),
]
