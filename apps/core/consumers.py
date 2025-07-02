import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

from .models import ChatSession, Message
from .services import ChatService


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_service = ChatService()
        self.session_id = None
        self.session = None

    async def connect(self):
        # Extract session_id from URL route
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        
        if not self.session_id:
            # Create new session if none provided
            self.session_id = str(uuid.uuid4())
            
        # Create or get session
        self.session = await self.get_or_create_session(self.session_id)
        
        # Join session group
        await self.channel_layer.group_add(
            f"chat_{self.session_id}",
            self.channel_name
        )
        
        await self.accept()
        
        # Send session info to client
        await self.send(text_data=json.dumps({
            'type': 'session_info',
            'session_id': str(self.session_id),
            'message': 'Connected to chat session'
        }))

    async def disconnect(self, close_code):
        # Leave session group
        if self.session_id:
            await self.channel_layer.group_discard(
                f"chat_{self.session_id}",
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))

    async def handle_chat_message(self, data):
        user_message = data.get('message', '').strip()
        
        if not user_message:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message cannot be empty'
            }))
            return

        try:
            # Save user message
            user_msg = await self.save_message(
                session=self.session,
                sender='human',
                text=user_message
            )
            
            # Send user message confirmation
            await self.send(text_data=json.dumps({
                'type': 'message_saved',
                'message': {
                    'id': user_msg.id,
                    'sender': 'human',
                    'text': user_message,
                    'created': user_msg.created.isoformat()
                }
            }))
            
            # Send typing indicator
            await self.send(text_data=json.dumps({
                'type': 'ai_typing',
                'message': 'AI is thinking...'
            }))
            
            # Get session messages for context
            session_messages = await self.get_session_messages(self.session)
            
            # Get AI response with streaming
            ai_response_text = ""
            
            # Send start of AI response
            await self.send(text_data=json.dumps({
                'type': 'ai_response_start'
            }))
            
            # Stream LLM response
            async for token in self.chat_service.get_streaming_response(user_message, session_messages):
                ai_response_text += token
                
                # Send each token to client
                await self.send(text_data=json.dumps({
                    'type': 'ai_response_token',
                    'token': token,
                    'partial_text': ai_response_text
                }))
            
            # Send end of AI response
            await self.send(text_data=json.dumps({
                'type': 'ai_response_end'
            }))
            
            # Save complete AI response
            ai_msg = await self.save_message(
                session=self.session,
                sender='ai',
                text=ai_response_text
            )
            
            # Send final message confirmation
            await self.send(text_data=json.dumps({
                'type': 'ai_message_saved',
                'message': {
                    'id': ai_msg.id,
                    'sender': 'ai',
                    'text': ai_response_text,
                    'created': ai_msg.created.isoformat()
                }
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error generating AI response: {str(e)}'
            }))

    @database_sync_to_async
    def get_or_create_session(self, session_id):
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            session = ChatSession.objects.create(id=session_id)
        return session

    @database_sync_to_async
    def save_message(self, session, sender, text):
        return Message.objects.create(
            session=session,
            sender=sender,
            text=text
        )

    @database_sync_to_async
    def get_session_messages(self, session):
        return list(session.messages.all().order_by('created'))
