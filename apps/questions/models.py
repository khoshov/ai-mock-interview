from django.db import models

from core.models import Category


class Question(models.Model):
    QUESTION_TYPES = [
        ("open", "Open-ended"),
        ("choice", "Multiple Choice"),
    ]
    DIFFICULTY_LEVELS = [
        ("junior", "Junior"),
        ("middle", "Middle"),
        ("senior", "Senior"),
    ]

    text = models.TextField(
        verbose_name="Текст вопроса", help_text="Введите текст вопроса"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Категория",
        help_text="Выберите категорию вопроса",
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_LEVELS,
        verbose_name="Уровень сложности",
        help_text="Выберите уровень сложности",
    )
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        verbose_name="Тип вопроса",
        help_text="Выберите тип вопроса",
    )
    correct_answer = models.TextField(
        blank=True,
        verbose_name="Правильный ответ",
        help_text="Введите правильный ответ",
    )
    explanation = models.TextField(
        blank=True, verbose_name="Объяснение", help_text="Введите объяснение ответа"
    )

    def __str__(self):
        return self.text[:50]
