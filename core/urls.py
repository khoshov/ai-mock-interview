from django.urls import path

from .views import chat, home, chat_view, new_chat

app_name = 'core'

urlpatterns = [
    path('num', chat, name='chat'),
    path('', home, name='home'),
    path('new/', new_chat, name='new_chat'),
    path('<str:id>/', chat_view, name='chats'),
]
