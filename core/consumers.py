# import json
# from random import randint
# from asyncio import sleep

# from channels.generic.websocket import AsyncWebsocketConsumer


# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         await self.accept()

#         for i in range(1000):
#             num = randint(1, 100)
#             await self.send(json.dumps({'value': num}))
#             await sleep(1)

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.base import AsyncCallbackHandler


class WSCallback(AsyncCallbackHandler):
    """Передаёт каждый токен прямо в WebSocket."""
    def __init__(self, ws_consumer):
        self.ws = ws_consumer

    async def on_llm_new_token(self, token: str, **kwargs):
        # Отправляем как текст; можно упаковать в JSON {type:"token", data:token}
        await self.ws.send(text_data=token)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Принимаем вопрос от клиента, запускаем LLM со стримингом.
        После завершения шлём специальный маркер — клиент поймёт, что вывод закончен.
        """
        user_prompt = text_data.strip()

        callback = WSCallback(self)

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            streaming=True,
            temperature=0.7,
            callbacks=[callback],
        )

        # agenerate — асинхронный вызов; ответ целиком нам даже не нужен:
        await llm.agenerate([[user_prompt]])

        await self.send(text_data="[END]")
