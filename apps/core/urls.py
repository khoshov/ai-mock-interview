from django.urls import path

from .views import (
    chat,
    get_tts_models,
    interview,
    switch_tts_model,
    test_tts,
    test_tts_api,
)

app_name = "core"

urlpatterns = [
    path("", chat, name="chat"),
    path("interview/", interview, name="interview"),
    path("test-tts/", test_tts, name="test_tts"),
    path("api/test-tts/", test_tts_api, name="test_tts_api"),
    path("api/tts-models/", get_tts_models, name="get_tts_models"),
    path("api/switch-tts-model/", switch_tts_model, name="switch_tts_model"),
]
