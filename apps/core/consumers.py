import asyncio
import json

import markdown
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from config.settings import OPENAI_API_KEY

# Инициализация модели
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=OPENAI_API_KEY,
    streaming=True,
)

# Промпт для чата
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Ты дружелюбный помощник."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# История сообщений
history_store = {}

def markdown_to_html(text):
    return markdown.markdown(
        text,
        extensions=['fenced_code', 'codehilite']
    )


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


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.session_id = self.scope["session"].session_key or self.channel_name
#         await self.accept()

#     async def receive(self, text_data):

#         data = json.loads(text_data)
#         user_message = data.get("message", "")

#         # Получаем историю
#         history = get_history(self.session_id)
#         history.add_user_message(user_message)

#         # Получаем ответ
#         response = await chain.ainvoke(
#             {"messages": history.messages},
#             config={"configurable": {"session_id": self.session_id}},
#         )
#         answer = response.content

#         # Преобразуем Markdown-ответ в HTML
#         answer_html = markdown_to_html(answer)

#         history.add_ai_message(answer_html)

#         await self.send(text_data=json.dumps({"answer": answer_html}))

async def stream_llm_response(chain, messages, session_id):
    async for chunk in chain.astream(
        {"messages": messages},
        config={"configurable": {"session_id": session_id}},
    ):
        if hasattr(chunk, 'content') and chunk.content:
            yield chunk.content
            await asyncio.sleep(0.01)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["session"].session_key or self.channel_name
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data.get("message", "")

        history = get_history(self.session_id)
        history.add_user_message(user_message)

        full_answer = ""
        async for chunk_text in stream_llm_response(chain, history.messages, self.session_id):
            full_answer += chunk_text
            await self.send(text_data=json.dumps({"answer_chunk": chunk_text}))
        await self.send(text_data=json.dumps({"answer_chunk": "END_OF_ANSWER"}))
        history.add_ai_message(full_answer)
