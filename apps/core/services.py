import random
from typing import Any

from interviews.models import Answer, ExpertAnswer, InterviewSession
from questions.models import Question

from django.contrib.auth.models import User
from django.db.models import Avg

from .models import Category


class InterviewService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_session: InterviewSession | None = None
        self.asked_questions = set()

    def start_interview(
        self, user: User, category: Category, difficulty: str
    ) -> InterviewSession:
        self.current_session = InterviewSession.objects.create(
            user=user, category=category, difficulty=difficulty
        )
        self.asked_questions.clear()
        return self.current_session

    def get_next_question(self) -> Question | None:
        if not self.current_session:
            return None

        available_questions = Question.objects.filter(
            category=self.current_session.category,
            difficulty=self.current_session.difficulty,
        ).exclude(id__in=self.asked_questions)

        if not available_questions.exists():
            return None

        question = random.choice(available_questions)
        self.asked_questions.add(question.id)
        return question

    def save_answer(self, question: Question, user_answer: str) -> Answer:
        if not self.current_session:
            raise ValueError("No active interview session")

        expert_answer, created = ExpertAnswer.objects.get_or_create(
            question=question, defaults={"text": question.correct_answer}
        )

        answer = Answer.objects.create(
            session=self.current_session,
            user=self.current_session.user,
            question=question,
            user_answer=user_answer,
            expert_answer=expert_answer,
        )

        return answer

    def finish_interview(self):
        if self.current_session:
            from django.utils import timezone

            self.current_session.end_time = timezone.now()
            self.current_session.save()

    def get_session_stats(self) -> dict[str, Any]:
        if not self.current_session:
            return {}

        answers = Answer.objects.filter(session=self.current_session)
        total_questions = answers.count()

        if total_questions == 0:
            return {"total_questions": 0, "avg_score": 0, "valid_answers": 0}

        valid_answers = answers.filter(is_valid=True).count()
        avg_score = (
            answers.filter(llm_score__isnull=False).aggregate(avg=Avg("llm_score"))[
                "avg"
            ]
            or 0
        )

        return {
            "total_questions": total_questions,
            "avg_score": round(avg_score, 2),
            "valid_answers": valid_answers,
        }


class InterviewSessionStore:
    _sessions = {}

    @classmethod
    def get_service(cls, session_id: str) -> InterviewService:
        if session_id not in cls._sessions:
            cls._sessions[session_id] = InterviewService(session_id)
        return cls._sessions[session_id]

    @classmethod
    def clear_session(cls, session_id: str):
        if session_id in cls._sessions:
            del cls._sessions[session_id]
