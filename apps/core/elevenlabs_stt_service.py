import os
import tempfile
from typing import Optional

from elevenlabs import ElevenLabs


class ElevenLabsSTTService:
    """ElevenLabs Speech-to-Text сервис для распознавания речи"""

    # Поддерживаемые модели STT
    SUPPORTED_STT_MODELS = {
        "scribe_v1": {
            "name": "Scribe v1",
            "description": "Основная модель для транскрибации речи",
            "recommended": True,
        },
        "scribe_v1_experimental": {
            "name": "Scribe v1 Experimental", 
            "description": "Экспериментальная версия с новыми возможностями",
            "recommended": False,
        },
    }

    # Поддерживаемые языки для STT
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ru": "Russian", 
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "pl": "Polish",
        "nl": "Dutch",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "auto": "Auto-detect",
    }

    def __init__(self, api_key: str, default_language: str = "auto"):
        """
        Инициализация ElevenLabs STT сервиса
        
        Args:
            api_key: API ключ ElevenLabs
            default_language: Язык по умолчанию для распознавания
        """
        self.client = ElevenLabs(api_key=api_key)
        self.default_language = default_language
        
        # Модель для STT - используем правильную модель
        self.model_id = "scribe_v1"  # Основная STT модель
        self.model_id_experimental = "scribe_v1_experimental"  # Экспериментальная модель
        
    def get_supported_languages(self) -> dict:
        """Возвращает список поддерживаемых языков"""
        return self.SUPPORTED_LANGUAGES
    
    def get_supported_models(self) -> dict:
        """Возвращает список поддерживаемых STT моделей"""
        return self.SUPPORTED_STT_MODELS
    
    def get_current_model_info(self) -> dict:
        """Возвращает информацию о текущей модели"""
        return {
            "primary_model": self.model_id,
            "fallback_model": self.model_id_experimental,
            "model_info": self.SUPPORTED_STT_MODELS.get(self.model_id, {}),
        }

    def set_default_language(self, language: str):
        """
        Устанавливает язык по умолчанию
        
        Args:
            language: Код языка (например, 'en', 'ru', 'auto')
        """
        if language in self.SUPPORTED_LANGUAGES:
            self.default_language = language
            print(f"🌐 Установлен язык STT: {self.SUPPORTED_LANGUAGES[language]}")
        else:
            print(f"❌ Неподдерживаемый язык: {language}")

    def is_available(self) -> bool:
        """Проверяет доступность ElevenLabs STT сервиса"""
        try:
            # Проверяем доступность пользователя
            user_info = self.client.user.get()
            print(f"🔍 ElevenLabs user доступен, лимит символов: {getattr(user_info.subscription, 'character_limit', 'неизвестно')}")
            
            # Проверяем доступность STT API
            if hasattr(self.client, 'speech_to_text'):
                stt_client = self.client.speech_to_text
                if hasattr(stt_client, 'convert'):
                    print("🔍 ElevenLabs STT: API метод доступен")
                    return True
                else:
                    print("🔍 ElevenLabs STT: метод convert не найден")
                    return False
            else:
                print("🔍 ElevenLabs STT: speech_to_text не доступен в данной версии API")
                return False
                
        except Exception as e:
            print(f"🔍 ElevenLabs STT проверка недоступна: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                print("   💡 Ошибка аутентификации - проверьте ELEVENLABS_API_KEY")
            elif "403" in str(e) or "Forbidden" in str(e):
                print("   💡 Доступ запрещен - возможны географические ограничения")
            return False

    def transcribe_audio_file(
        self, 
        audio_file_path: str, 
        language: Optional[str] = None,
        remove_background_noise: bool = True
    ) -> Optional[str]:
        """
        Транскрибирует аудио файл в текст
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык для распознавания (если None, используется default_language)
            remove_background_noise: Убирать фоновый шум
            
        Returns:
            Распознанный текст или None при ошибке
        """
        if not os.path.exists(audio_file_path):
            print(f"❌ Файл не найден: {audio_file_path}")
            return None

        target_language = language or self.default_language
        
        try:
            print(f"🎤 ElevenLabs STT: Транскрибируем {audio_file_path}")
            print(f"🌐 Язык: {self.SUPPORTED_LANGUAGES.get(target_language, target_language)}")
            
            with open(audio_file_path, "rb") as audio_file:
                # Используем ElevenLabs STT API с правильной моделью
                try:
                    # Пробуем основную модель scribe_v1
                    transcript_response = self.client.speech_to_text.convert(
                        file=audio_file,
                        model_id=self.model_id,
                    )
                    print(f"✅ Использована модель: {self.model_id}")
                except Exception as e:
                    if "invalid_model_id" in str(e) or "not a valid model_id" in str(e):
                        print(f"🔄 Модель {self.model_id} не работает, пробуем экспериментальную...")
                        # Перематываем файл и пробуем экспериментальную модель
                        audio_file.seek(0)
                        transcript_response = self.client.speech_to_text.convert(
                            file=audio_file,
                            model_id=self.model_id_experimental,
                        )
                        print(f"✅ Использована экспериментальная модель: {self.model_id_experimental}")
                    elif "unexpected keyword argument 'model_id'" in str(e):
                        print("🔄 model_id не поддерживается, пробуем без него...")
                        # Перематываем файл и пробуем без model_id
                        audio_file.seek(0)
                        transcript_response = self.client.speech_to_text.convert(
                            file=audio_file,
                        )
                        print("✅ Использован вызов без model_id")
                    else:
                        raise e
                
                transcript = transcript_response.text if hasattr(transcript_response, 'text') else str(transcript_response)
                
                print(f"💬 Результат STT: {transcript}")
                return transcript.strip() if transcript else None

        except Exception as e:
            print(f"❌ Ошибка ElevenLabs STT: {e}")
            return None

    def transcribe_audio_bytes(
        self, 
        audio_bytes: bytes, 
        language: Optional[str] = None,
        audio_format: str = "webm",
        remove_background_noise: bool = True
    ) -> Optional[str]:
        """
        Транскрибирует аудио из байтов в текст
        
        Args:
            audio_bytes: Аудио данные в байтах
            language: Язык для распознавания
            audio_format: Формат аудио файла
            remove_background_noise: Убирать фоновый шум
            
        Returns:
            Распознанный текст или None при ошибке
        """
        if not audio_bytes:
            print("❌ Пустые аудио данные")
            return None

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name

        try:
            # Транскрибируем файл
            result = self.transcribe_audio_file(
                temp_file_path, 
                language=language,
                remove_background_noise=remove_background_noise
            )
            return result
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def transcribe_with_fallback_languages(
        self, 
        audio_file_path: str, 
        languages: list[str] = None
    ) -> Optional[tuple[str, str]]:
        """
        Пытается транскрибировать с несколькими языками
        
        Args:
            audio_file_path: Путь к аудио файлу
            languages: Список языков для попыток (по умолчанию ['auto', 'en', 'ru'])
            
        Returns:
            Кортеж (текст, язык) или None при неудаче
        """
        if languages is None:
            languages = ['auto', 'en', 'ru']

        for lang in languages:
            try:
                result = self.transcribe_audio_file(audio_file_path, language=lang)
                if result and result.strip():
                    return (result, lang)
            except Exception as e:
                print(f"❌ Попытка с языком {lang} не удалась: {e}")
                continue
                
        print("❌ Все попытки транскрибации не удались")
        return None

    def batch_transcribe(
        self, 
        audio_files: list[str], 
        language: Optional[str] = None
    ) -> dict[str, Optional[str]]:
        """
        Транскрибирует несколько файлов
        
        Args:
            audio_files: Список путей к аудио файлам
            language: Язык для распознавания
            
        Returns:
            Словарь {файл: транскрипция}
        """
        results = {}
        
        for audio_file in audio_files:
            try:
                transcript = self.transcribe_audio_file(audio_file, language=language)
                results[audio_file] = transcript
            except Exception as e:
                print(f"❌ Ошибка транскрибации {audio_file}: {e}")
                results[audio_file] = None
                
        return results

    def get_usage_info(self) -> dict:
        """
        Получает информацию об использовании API
        
        Returns:
            Информация о лимитах и использовании
        """
        try:
            user_info = self.client.user.get()
            return {
                "character_count": getattr(user_info.subscription, 'character_count', 0),
                "character_limit": getattr(user_info.subscription, 'character_limit', 0),
                "can_extend_character_limit": getattr(user_info.subscription, 'can_extend_character_limit', False),
                "allowed_to_extend_character_limit": getattr(user_info.subscription, 'allowed_to_extend_character_limit', False),
            }
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {e}")
            return {}


# Заглушка для обратной совместимости
class BackwardCompatibleSTTService:
    """Сервис для обратной совместимости со старым API"""
    
    def __init__(self, elevenlabs_service: ElevenLabsSTTService):
        self.elevenlabs = elevenlabs_service

    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """Совместимость с старым API whisper_service"""
        return self.elevenlabs.transcribe_audio_file(audio_file_path)
    
    def is_available(self) -> bool:
        return self.elevenlabs.is_available()
        
    def transcribe_audio_bytes(self, audio_bytes: bytes, audio_format: str = "webm") -> Optional[str]:
        """Транскрибация из байтов"""
        return self.elevenlabs.transcribe_audio_bytes(audio_bytes, audio_format=audio_format)