import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .elevenlabs_service import tts_service


def index(request):
    return render(request, "index.html")


def chat(request):
    return render(request, "index.html")


def interview(request):
    return render(request, "index.html")


@csrf_exempt
@require_http_methods(["POST"])
def test_tts_api(request):
    try:
        data = json.loads(request.body)
        text = data.get("text", "")

        if not text.strip():
            return JsonResponse({"error": "Текст не предоставлен"}, status=400)

        if not tts_service.is_available():
            return JsonResponse({"error": "TTS сервис недоступен"}, status=503)

        # Генерируем аудио
        audio_base64 = tts_service.text_to_audio_base64(text)

        return JsonResponse(
            {
                "success": True,
                "audio_base64": audio_base64,
                "text_length": len(text),
                "audio_size": len(audio_base64),
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_tts_models(request):
    """Получить список доступных TTS моделей"""
    try:
        models = tts_service.get_available_models()
        current = tts_service.get_current_model_info()

        return JsonResponse(
            {"available_models": models, "current_model": current, "success": True}
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def switch_tts_model(request):
    """Переключить TTS модель"""
    try:
        data = json.loads(request.body)
        model_name = data.get("model_name", "")

        if not model_name:
            return JsonResponse({"error": "Имя модели не предоставлено"}, status=400)

        success = tts_service.switch_model(model_name)

        if success:
            current = tts_service.get_current_model_info()
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Модель переключена на {model_name}",
                    "current_model": current,
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Не удалось переключить на модель {model_name}",
                },
                status=500,
            )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
