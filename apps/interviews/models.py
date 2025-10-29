from django.contrib.auth.models import User
from django.db import models

from core.models import Category
from questions.models import Question


class InterviewSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ("junior", "Junior"),
            ("middle", "Middle"),
            ("senior", "Senior"),
        ],
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Session #{self.id} by {self.user}"


class Answer(models.Model):
    session = models.ForeignKey(
        InterviewSession, on_delete=models.CASCADE, related_name="answers"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.TextField(blank=True)
    llm_score = models.FloatField(
        null=True, blank=True, help_text="Оценка соответствия в процентах"
    )
    llm_comment = models.TextField(
        blank=True, help_text="Что не раскрыто в ответе пользователя"
    )
    detailed_analysis = models.JSONField(
        default=dict, blank=True, help_text="Детальный анализ ответа по критериям"
    )
    is_valid = models.BooleanField(
        default=True, help_text="True — ответ релевантен, False — пустой или не по теме"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user} (Q{self.question.id}, S{self.session.id}) | Score: {self.llm_score}"
