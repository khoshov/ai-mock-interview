import asyncio
import json
import os
import tempfile
from enum import Enum
from typing import TYPE_CHECKING

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import PermissionDeniedError

from django.contrib.auth import get_user_model

from interviews.models import Answer
from questions.models import Question

from .llm_analyzer import LLMAnswerAnalyzer
from .models import Category
from .services import InterviewSessionStore
from .elevenlabs_service import tts_service, stt_service

if TYPE_CHECKING:
    from questions.models import Question


class InterviewState(Enum):
    AWAITING_NAME = "awaiting_name"
    AWAITING_CATEGORY = "awaiting_category"
    AWAITING_DIFFICULTY = "awaiting_difficulty"
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
        self.state = InterviewState.AWAITING_NAME
        self.current_question: Question | None = None
        self.user = None
        self.tts_enabled = False
        self.user_name = None
        self.available_categories = []
        self.chosen_category = None
        self.difficulty_levels = {
            "1": "junior",
            "2": "middle",
            "3": "senior",
        }

    async def connect(self):
        self.session_id = self.scope["session"].session_key or self.channel_name
        self.interview_service = InterviewSessionStore.get_service(self.session_id)
        self.user = await self.get_user()

        await self.accept()
        await self.send_message("👋 Привет! Я ваш виртуальный интервьюер.")
        await self.send_message("Как я могу к вам обращаться?")

    async def disconnect(self, close_code):
        if self.interview_service:
            await database_sync_to_async(self.interview_service.finish_interview)()
        InterviewSessionStore.clear_session(self.session_id)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                message = data.get("message", "").strip()

                if "enable_tts" in data:
                    self.tts_enabled = data.get("enable_tts", False)

                if not message:
                    await self.send_message("Пожалуйста, введите сообщение.")
                    return

                state_handlers = {
                    InterviewState.AWAITING_NAME: self.handle_name,
                    InterviewState.AWAITING_CATEGORY: self.handle_category_selection,
                    InterviewState.AWAITING_DIFFICULTY: self.handle_difficulty_selection,
                    InterviewState.ASKING: self.handle_start_answer,
                    InterviewState.ANSWERING: self.handle_answer,
                    InterviewState.FEEDBACK: self.handle_next_question,
                }

                handler = state_handlers.get(self.state)
                if handler:
                    await handler(message)
                else:
                    await self.send_message("Интервью завершено.")

            except json.JSONDecodeError:
                await self.send_message("Ошибка обработки сообщения.")
        elif bytes_data:
            await self.handle_audio(bytes_data)

    async def handle_name(self, name: str):
        self.user_name = name
        await self.send_message(f"Приятно познакомиться, {self.user_name}!")
        await self.prompt_for_category()

    async def prompt_for_category(self):
        self.available_categories = await database_sync_to_async(list)(Category.objects.all())
        if not self.available_categories:
            await self.send_message("❌ К сожалению, в базе данных пока нет ни одной темы для интервью.")
            return

        category_list = "\n".join(
            [f"{i + 1}. {cat.name}" for i, cat in enumerate(self.available_categories)]
        )
        await self.send_message(f"Выберите тему для интервью (введите номер или название):\n{category_list}")
        self.state = InterviewState.AWAITING_CATEGORY

    async def handle_category_selection(self, choice: str):
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(self.available_categories):
                self.chosen_category = self.available_categories[choice_idx]
            else:
                self.chosen_category = None
        except ValueError:
            self.chosen_category = next((cat for cat in self.available_categories if cat.name.lower() == choice.lower()), None)

        if self.chosen_category:
            await self.prompt_for_difficulty()
        else:
            await self.send_message("Неверный выбор. Пожалуйста, введите номер или название из списка.")

    async def prompt_for_difficulty(self):
        difficulty_list = "\n".join([f"{i}. {level.capitalize()}" for i, level in self.difficulty_levels.items()])
        await self.send_message(f"Отлично! Теперь выберите уровень сложности:\n{difficulty_list}")
        self.state = InterviewState.AWAITING_DIFFICULTY

    async def handle_difficulty_selection(self, choice: str):
        chosen_level_name = self.difficulty_levels.get(choice.lower())
        if not chosen_level_name:
             chosen_level_name = choice.lower() if choice.lower() in self.difficulty_levels.values() else None

        if not chosen_level_name:
            await self.send_message("Неверный выбор. Пожалуйста, введите номер или название уровня.")
            return

        has_questions = await database_sync_to_async(
            Question.objects.filter(category=self.chosen_category, difficulty=chosen_level_name).exists
        )()

        if has_questions:
            await self.setup_interview(self.chosen_category, chosen_level_name)
        else:
            await self.send_message(f"К сожалению, для темы '{self.chosen_category.name}' и уровня '{chosen_level_name}' пока нет вопросов.")
            await self.prompt_for_category()

    async def handle_audio(self, audio_data):
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".webm"
            ) as temp_audio_file:
                temp_audio_file.write(audio_data)
                temp_audio_file_path = temp_audio_file.name

            transcribed_text = await asyncio.to_thread(
                stt_service.transcribe_audio, temp_audio_file_path
            )

            os.remove(temp_audio_file_path)

            if transcribed_text:
                await self.send(
                    text_data=json.dumps(
                        {"type": "transcription_result", "transcript": transcribed_text}
                    )
                )
            else:
                await self.send_message(
                    "Не удалось распознать речь. Попробуйте еще раз."
                )

        except Exception as e:
            await self.send_message(f"Ошибка при обработке аудио: {e}")

    async def setup_interview(self, category: Category, difficulty: str):
        await database_sync_to_async(self.interview_service.start_interview)(
            self.user, category, difficulty
        )
        self.state = InterviewState.SETUP
        await self.send_message("✅ Отлично, все готово!")
        await self.send_message(f"📂 Категория: {category.name}")
        await self.send_message(f"📊 Уровень: {difficulty.capitalize()}")
        await self.send_message(f"🚀 Начинаем, {self.user_name}! Удачи!")
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
        await self.send_message(
            "💭 Напишите ваш ответ в чат или используйте голосовое сообщение."
        )

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

        try:
            await self.send_message(f"🔄 Анализирую ваш ответ, {self.user_name}...")

            analysis = await self.llm_analyzer.analyze_answer(
                self.current_question.text, self.current_question.correct_answer, message
            )

            await self.update_answer_analysis(answer, analysis)

            await self.send_message(f"📊 **Оценка:** {analysis['score']}/100")
            await self.send_message("💬 **Обратная связь:**")

            self.state = InterviewState.FEEDBACK

            full_feedback = ""
            text_buffer = ""

            async for chunk in self.llm_analyzer.generate_feedback(
                self.current_question.text, message, analysis
            ):
                full_feedback += chunk
                await self.send(text_data=json.dumps({"answer_chunk": chunk}))

                if self.tts_enabled and tts_service and tts_service.is_available():
                    text_buffer += chunk

                    sentence_endings = [".", "!", "?", "\n"]
                    for ending in sentence_endings:
                        if ending in text_buffer:
                            sentences = text_buffer.split(ending)
                            for sentence in sentences[:-1]:
                                sentence = sentence.strip()
                                if sentence and len(sentence) > 10:
                                    try:
                                        audio_b64 = tts_service.text_to_audio_base64(sentence)
                                        await self.send(text_data=json.dumps({"audio_chunk": audio_b64, "audio_text": sentence}))
                                    except Exception as e:
                                        print(f"TTS error: {e}")
                            text_buffer = sentences[-1]
                            break

            if self.tts_enabled and tts_service and tts_service.is_available() and text_buffer.strip() and len(text_buffer.strip()) > 10:
                try:
                    audio_b64 = tts_service.text_to_audio_base64(text_buffer.strip())
                    await self.send(text_data=json.dumps({"audio_chunk": audio_b64, "audio_text": text_buffer.strip()}))
                except Exception as e:
                    print(f"TTS error: {e}")

            await self.send(text_data=json.dumps({"answer_chunk": "END_OF_ANSWER"}))
            await asyncio.sleep(1)
            await self.send_message("➡️ Напишите 'далее' для следующего вопроса или 'стоп' для завершения.")
        
        except PermissionDeniedError as e:
            if "unsupported_country_region_territory" in str(e):
                print("API-сервис недоступен из-за региональных ограничений.")
                await self.send_message("Сервис временно недоступен из-за региональных ограничений, попробуйте позже.")
                self.state = InterviewState.FEEDBACK
                await self.send_message("➡️ Напишите 'далее' для следующего вопроса или 'стоп' для завершения.")
            else:
                print(f"Произошла ошибка доступа к API: {e}")
                await self.send_message("Произошла ошибка доступа к API. Пожалуйста, проверьте ваши ключи и разрешения.")
                self.state = InterviewState.FEEDBACK
                raise

    async def handle_next_question(self, message: str):
        if message.lower() in ["далее", "next", "следующий"]:
            await self.ask_next_question()
        elif message.lower() in ["стоп", "stop", "завершить"]:
            await self.finish_interview()
        else:
            await self.send_message("Напишите 'далее' для продолжения или 'стоп' для завершения.")

    async def finish_interview(self):
        self.state = InterviewState.FINISHED
        await database_sync_to_async(self.interview_service.finish_interview)()
        stats = await database_sync_to_async(self.interview_service.get_session_stats)()

        await self.send_message(f"🏁 **Интервью завершено, {self.user_name}!**")
        await self.send_message("📈 **Ваша итоговая статистика:**")
        await self.send_message(f"• Всего вопросов: {stats.get('total_questions', 0)}")
        await self.send_message(f"• Средняя оценка: {stats.get('avg_score', 0)}")
        await self.send_message(f"• Валидных ответов: {stats.get('valid_answers', 0)}")
        await self.send_message("Спасибо за участие! 👋")

    async def send_message(self, message: str):
        await self.send(text_data=json.dumps({"answer_chunk": message + "\n\n"}))

        if self.tts_enabled and tts_service and tts_service.is_available() and message.strip():
            try:
                clean_message = message.replace("**", "").replace("*", "").replace("#", "").strip()
                if len(clean_message) > 5:
                    audio_b64 = tts_service.text_to_audio_base64(clean_message)
                    await self.send(text_data=json.dumps({"audio_chunk": audio_b64, "audio_text": clean_message}))
            except Exception as e:
                print(f"TTS error in send_message: {e}")

    @database_sync_to_async
    def get_user(self):
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="anonymous",
            defaults={"first_name": "Anonymous", "last_name": "User"},
        )
        return user

    @database_sync_to_async
    def update_answer_analysis(self, answer: Answer, analysis: dict):
        answer.llm_score = analysis["score"]
        answer.llm_comment = analysis["comment"]
        answer.is_valid = analysis["is_valid"]
        answer.detailed_analysis = analysis.get("detailed_analysis", {})
        answer.save()
