from django.urls import path

from .views import (
    index,
    chat,
    get_tts_models,
    interview,
    switch_tts_model,
    test_tts_api,
)

app_name = "core"

urlpatterns = [
    path("", index, name="index"),
    path("chat/", chat, name="chat"),
    path("interview/", interview, name="interview"),
    path("api/test-tts/", test_tts_api, name="test_tts_api"),
    path("api/tts-models/", get_tts_models, name="get_tts_models"),
    path("api/switch-tts-model/", switch_tts_model, name="switch_tts_model"),
]
