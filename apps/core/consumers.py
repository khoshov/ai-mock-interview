import asyncio
import json

import markdown
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from config.settings import OPENAI_API_KEY

from .tts_service import tts_service

# Инициализация модели
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=OPENAI_API_KEY,
    streaming=True,
)

# Промпт для чата
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Ты дружелюбный помощник при прохождении технического интервью."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# История сообщений
history_store = {}


def markdown_to_html(text):
    return markdown.markdown(text, extensions=["fenced_code", "codehilite"])


def get_history(session_id):
    if session_id not in history_store:
        history_store[session_id] = InMemoryChatMessageHistory()
    return history_store[session_id]


# Цепочка с историей сообщений
chain = RunnableWithMessageHistory(
    prompt | llm,
    get_session_history=get_history,
    input_messages_key="messages",
    history_messages_key="messages",
)


async def stream_llm_response(chain, messages, session_id):
    async for chunk in chain.astream(
        {"messages": messages},
        config={"configurable": {"session_id": session_id}},
    ):
        if hasattr(chunk, "content") and chunk.content:
            yield chunk.content
            await asyncio.sleep(0.01)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["session"].session_key or self.channel_name
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data.get("message", "")
        enable_tts = data.get("enable_tts", False)

        history = get_history(self.session_id)
        history.add_user_message(user_message)

        full_answer = ""

        if enable_tts and tts_service.is_available():
            # Создаем генератор текстовых чанков
            async def text_chunks():
                async for chunk_text in stream_llm_response(
                    chain, history.messages, self.session_id
                ):
                    yield chunk_text

            # Обрабатываем текст и аудио параллельно
            text_buffer = ""
            async for chunk_text in stream_llm_response(
                chain, history.messages, self.session_id
            ):
                full_answer += chunk_text
                text_buffer += chunk_text

                # Отправляем текстовый чанк
                await self.send(text_data=json.dumps({"answer_chunk": chunk_text}))

                # Проверяем, есть ли завершенные предложения для озвучки
                sentence_endings = [".", "!", "?", "\n"]
                for ending in sentence_endings:
                    if ending in text_buffer:
                        sentences = text_buffer.split(ending)
                        for sentence in sentences[:-1]:
                            sentence = sentence.strip()
                            if sentence and len(sentence) > 10:
                                try:
                                    audio_b64 = tts_service.text_to_audio_base64(
                                        sentence
                                    )
                                    await self.send(
                                        text_data=json.dumps(
                                            {
                                                "audio_chunk": audio_b64,
                                                "audio_text": sentence,
                                            }
                                        )
                                    )
                                except Exception as e:
                                    print(f"TTS error: {e}")
                        text_buffer = sentences[-1]
                        break

            # Обработаем остаток текста для TTS
            if text_buffer.strip() and len(text_buffer.strip()) > 10:
                try:
                    audio_b64 = tts_service.text_to_audio_base64(text_buffer.strip())
                    await self.send(
                        text_data=json.dumps(
                            {
                                "audio_chunk": audio_b64,
                                "audio_text": text_buffer.strip(),
                            }
                        )
                    )
                except Exception as e:
                    print(f"TTS error: {e}")
        else:
            # Обычный режим без TTS
            async for chunk_text in stream_llm_response(
                chain, history.messages, self.session_id
            ):
                full_answer += chunk_text
                await self.send(text_data=json.dumps({"answer_chunk": chunk_text}))

        await self.send(text_data=json.dumps({"answer_chunk": "END_OF_ANSWER"}))
        history.add_ai_message(full_answer)
