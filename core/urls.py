from django.urls import path

from .views import chat

app_name = 'core'

urlpatterns = [
    path('', chat, name='chat'),
]