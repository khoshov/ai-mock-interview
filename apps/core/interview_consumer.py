import asyncio
import json
from enum import Enum

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth import get_user_model

from .llm_analyzer import LLMAnswerAnalyzer
from .models import Category
from .services import InterviewSessionStore
from interviews.models import Answer
from questions.models import Question


class InterviewState(Enum):
    SETUP = "setup"
    ASKING = "asking"
    ANSWERING = "answering"
    FEEDBACK = "feedback"
    FINISHED = "finished"


class InterviewConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.interview_service = None
        self.llm_analyzer = LLMAnswerAnalyzer()
        self.state = InterviewState.SETUP
        self.current_question: Question | None = None
        self.user = None

    async def connect(self):
        self.session_id = self.scope["session"].session_key or self.channel_name
        self.interview_service = InterviewSessionStore.get_service(self.session_id)

        self.user = await self.get_user()

        await self.accept()
        await self.send_message("🎯 Добро пожаловать на техническое интервью!")
        await self.send_message("Я ваш виртуальный интервьюер. Давайте начнем!")
        await self.send_setup_options()

    async def disconnect(self, close_code):
        if self.interview_service:
            await database_sync_to_async(self.interview_service.finish_interview)()
        InterviewSessionStore.clear_session(self.session_id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()

            if not message:
                await self.send_message("Пожалуйста, введите сообщение.")
                return

            if self.state == InterviewState.SETUP:
                await self.handle_setup(message)
            elif self.state == InterviewState.ASKING:
                await self.handle_start_answer(message)
            elif self.state == InterviewState.ANSWERING:
                await self.handle_answer(message)
            elif self.state == InterviewState.FEEDBACK:
                await self.handle_next_question(message)
            else:
                await self.send_message("Интервью завершено.")

        except json.JSONDecodeError:
            await self.send_message("Ошибка обработки сообщения.")

    async def handle_setup(self, message: str):
        if message.lower() in ['старт', 'начать', 'start']:
            await self.setup_interview()
        else:
            await self.send_message("Напишите 'старт' для начала интервью.")

    async def setup_interview(self):
        categories = await database_sync_to_async(list)(Category.objects.all())

        if not categories:
            await self.send_message("❌ Нет доступных категорий вопросов.")
            return

        default_category = categories[0]
        default_difficulty = "middle"

        session = await database_sync_to_async(self.interview_service.start_interview)(
            self.user, default_category, default_difficulty
        )

        await self.send_message("✅ Интервью начато!")
        await self.send_message(f"📂 Категория: {default_category.name}")
        await self.send_message(f"📊 Уровень: {default_difficulty}")
        await self.ask_next_question()

    async def ask_next_question(self):
        self.current_question = await database_sync_to_async(
            self.interview_service.get_next_question
        )()

        if not self.current_question:
            await self.finish_interview()
            return

        self.state = InterviewState.ASKING
        await self.send_message(f"❓ **Вопрос:** {self.current_question.text}")
        await self.send_message("💭 Обдумайте ответ и напишите его, когда будете готовы.")

    async def handle_start_answer(self, message: str):
        self.state = InterviewState.ANSWERING
        await self.handle_answer(message)

    async def handle_answer(self, message: str):
        if not self.current_question:
            await self.send_message("Ошибка: нет активного вопроса.")
            return

        answer = await database_sync_to_async(self.interview_service.save_answer)(
            self.current_question, message
        )

        await self.send_message("🔄 Анализирую ваш ответ...")

        analysis = await self.llm_analyzer.analyze_answer(
            self.current_question.text,
            self.current_question.correct_answer,
            message
        )

        await self.update_answer_analysis(answer, analysis)

        await self.send_message(f"📊 **Оценка:** {analysis['score']}/100")
        await self.send_message("💬 **Обратная связь:**")

        self.state = InterviewState.FEEDBACK

        full_feedback = ""
        async for chunk in self.llm_analyzer.generate_feedback(
            self.current_question.text, message, analysis
        ):
            full_feedback += chunk
            await self.send(text_data=json.dumps({"answer_chunk": chunk}))

        await self.send(text_data=json.dumps({"answer_chunk": "END_OF_ANSWER"}))

        await asyncio.sleep(1)
        await self.send_message("➡️ Напишите 'далее' для следующего вопроса или 'стоп' для завершения.")

    async def handle_next_question(self, message: str):
        if message.lower() in ['далее', 'next', 'следующий']:
            await self.ask_next_question()
        elif message.lower() in ['стоп', 'stop', 'завершить']:
            await self.finish_interview()
        else:
            await self.send_message("Напишите 'далее' для продолжения или 'стоп' для завершения.")

    async def finish_interview(self):
        self.state = InterviewState.FINISHED
        await database_sync_to_async(self.interview_service.finish_interview)()

        stats = await database_sync_to_async(self.interview_service.get_session_stats)()

        await self.send_message("🏁 **Интервью завершено!**")
        await self.send_message("📈 **Статистика:**")
        await self.send_message(f"• Всего вопросов: {stats.get('total_questions', 0)}")
        await self.send_message(f"• Средняя оценка: {stats.get('avg_score', 0)}")
        await self.send_message(f"• Валидных ответов: {stats.get('valid_answers', 0)}")
        await self.send_message("Спасибо за участие в интервью! 👋")

    async def send_setup_options(self):
        await self.send_message("Для начала интервью напишите: **старт**")

    async def send_message(self, message: str):
        await self.send(text_data=json.dumps({
            "answer_chunk": message + "\n\n"
        }))

    @database_sync_to_async
    def get_user(self):
        UserModel = get_user_model()
        user, created = UserModel.objects.get_or_create(
            username='anonymous',
            defaults={'first_name': 'Anonymous', 'last_name': 'User'}
        )
        return user

    @database_sync_to_async
    def update_answer_analysis(self, answer: Answer, analysis: dict):
        answer.llm_score = analysis['score']
        answer.llm_comment = analysis['comment']
        answer.is_valid = analysis['is_valid']
        answer.detailed_analysis = analysis.get('detailed_analysis', {})
        answer.save()
