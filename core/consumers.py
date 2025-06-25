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
from .utils import generate_response  # ваша функция генерации ответа
from asgiref.sync import sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'chat_global'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_input = data['message']

        # Истории нет, только текущее сообщение
        ai_response = await self.get_ai_response(user_input)

        # Отправляем только тому, кто написал (или всем, если нужно)
        await self.send(text_data=json.dumps({
            'sender': 'human',
            'message': user_input
        }))
        await self.send(text_data=json.dumps({
            'sender': 'ai',
            'message': ai_response
        }))

    async def get_ai_response(self, user_input):
        # generate_response может принимать только текст, без истории
        return await sync_to_async(generate_response)(user_input, [])
    