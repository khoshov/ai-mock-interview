from django.urls import path

from .views import chat, interview

app_name = "core"

urlpatterns = [
    path("", chat, name="chat"),
    path("interview/", interview, name="interview"),
]
