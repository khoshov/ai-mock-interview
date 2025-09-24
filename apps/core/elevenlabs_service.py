"""
Интегрированный сервис ElevenLabs для TTS и STT
Заменяет локальные модели Whisper и Coqui TTS
"""

from config.settings import ELEVENLABS_API_KEY

from .elevenlabs_tts_service import ElevenLabsTTSService, BackwardCompatibleTTSService
from .elevenlabs_stt_service import ElevenLabsSTTService, BackwardCompatibleSTTService


# Инициализируем сервисы ElevenLabs
elevenlabs_tts = None
elevenlabs_stt = None
tts_service = None
stt_service = None

if ELEVENLABS_API_KEY:
    print(f"🔑 ElevenLabs API ключ найден (длина: {len(ELEVENLABS_API_KEY)} символов)")
    
    try:
        print("🚀 Инициализация ElevenLabs TTS...")
        elevenlabs_tts = ElevenLabsTTSService(
            api_key=ELEVENLABS_API_KEY,
            voice_id="rachel_en"  # Голос по умолчанию
        )
        
        # Создаем обратно совместимый сервис
        tts_service = BackwardCompatibleTTSService(elevenlabs_tts)
        
        if elevenlabs_tts.is_available():
            print("✅ ElevenLabs TTS успешно инициализирован")
        else:
            print("❌ ElevenLabs TTS недоступен (проверьте API ключ)")
            tts_service = None
            
    except Exception as e:
        print(f"❌ Ошибка инициализации ElevenLabs TTS: {e}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   💡 Проверьте правильность ELEVENLABS_API_KEY")
        tts_service = None

    try:
        print("🚀 Инициализация ElevenLabs STT...")
        elevenlabs_stt = ElevenLabsSTTService(
            api_key=ELEVENLABS_API_KEY,
            default_language="auto"
        )
        
        # Создаем обратно совместимый сервис
        stt_service = BackwardCompatibleSTTService(elevenlabs_stt)
        
        if elevenlabs_stt.is_available():
            print("✅ ElevenLabs STT успешно инициализирован")
        else:
            print("❌ ElevenLabs STT недоступен (проверьте API ключ)")
            stt_service = None
            
    except Exception as e:
        print(f"❌ Ошибка инициализации ElevenLabs STT: {e}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   💡 Проверьте правильность ELEVENLABS_API_KEY")
        stt_service = None
        
else:
    print("⚠️ ELEVENLABS_API_KEY не найден в переменных окружения")
    print("   Добавьте ELEVENLABS_API_KEY=your_api_key в файл .env")
    print("   Получить API ключ можно на https://elevenlabs.io/")


def get_tts_service():
    """Получить TTS сервис"""
    return tts_service


def get_stt_service(): 
    """Получить STT сервис"""
    return stt_service


def is_elevenlabs_available() -> bool:
    """Проверить доступность сервисов ElevenLabs"""
    return tts_service is not None and stt_service is not None


def get_elevenlabs_info() -> dict:
    """Получить информацию о сервисах ElevenLabs"""
    info = {
        "tts_available": tts_service is not None,
        "stt_available": stt_service is not None,
        "api_key_configured": bool(ELEVENLABS_API_KEY),
    }
    
    if elevenlabs_tts:
        info["tts_voice"] = elevenlabs_tts.get_current_voice_info()
        info["tts_usage"] = elevenlabs_tts.get_usage_info()
        
    if elevenlabs_stt:
        info["stt_language"] = elevenlabs_stt.default_language
        info["stt_supported_languages"] = elevenlabs_stt.get_supported_languages()
        
    return info


def switch_tts_voice(voice_identifier: str) -> bool:
    """Переключить голос TTS"""
    if elevenlabs_tts:
        return elevenlabs_tts.switch_voice(voice_identifier)
    return False


def switch_stt_language(language: str):
    """Переключить язык STT"""
    if elevenlabs_stt:
        elevenlabs_stt.set_default_language(language)


def configure_tts_voice_settings(**kwargs):
    """Настроить параметры голоса TTS"""
    if elevenlabs_tts:
        elevenlabs_tts.set_voice_settings(**kwargs)


# Экспортируем сервисы для обратной совместимости
# Эти переменные должны использоваться вместо старых tts_service и whisper_service
__all__ = [
    'tts_service',
    'stt_service', 
    'get_tts_service',
    'get_stt_service',
    'is_elevenlabs_available',
    'get_elevenlabs_info',
    'switch_tts_voice',
    'switch_stt_language',
    'configure_tts_voice_settings',
]