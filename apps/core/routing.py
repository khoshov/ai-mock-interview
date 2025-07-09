from django.urls import re_path

from .consumers import ChatConsumer
from .interview_consumer import InterviewConsumer

ws_urlpatterns = [
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),
    re_path(r"ws/interview/$", InterviewConsumer.as_asgi()),
]
