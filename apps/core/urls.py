from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('chat/', views.new_chat_view, name='new_chat'),
    path('chat/<uuid:session_id>/', views.chat_view, name='chat'),
    path('sessions/', views.chat_sessions_view, name='chat_sessions'),
    path('api/sessions/', views.api_chat_sessions, name='api_chat_sessions'),
]
