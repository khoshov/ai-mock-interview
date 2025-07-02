import asyncio
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from django.conf import settings


class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=True,
            temperature=0.7
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты помощник для подготовки к техническим интервью. "
                      "Задавай релевантные вопросы, анализируй ответы и давай полезную обратную связь. "
                      "Будь дружелюбным и конструктивным."),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        self.chain = self.prompt | self.llm

    async def get_streaming_response(self, user_message: str, session_messages: list = None) -> AsyncGenerator[str, None]:
        """
        Получить потоковый ответ от LLM
        """
        try:
            # Формируем историю сообщений
            messages = []
            
            if session_messages:
                for msg in session_messages:
                    if msg.sender == 'human':
                        messages.append(HumanMessage(content=msg.text))
                    elif msg.sender == 'ai':
                        messages.append(AIMessage(content=msg.text))
            
            # Добавляем текущее сообщение пользователя
            messages.append(HumanMessage(content=user_message))
            
            # Получаем потоковый ответ
            async for chunk in self.chain.astream({"messages": messages}):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    # Небольшая задержка для имитации печати
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            yield f"Произошла ошибка при генерации ответа: {str(e)}"

    async def get_response(self, user_message: str, session_messages: list = None) -> str:
        """
        Получить полный ответ от LLM (не потоковый)
        """
        response_parts = []
        async for token in self.get_streaming_response(user_message, session_messages):
            response_parts.append(token)
        
        return "".join(response_parts)