import base64
import io
from collections.abc import Generator
from typing import Optional

from elevenlabs import ElevenLabs
from elevenlabs.types import Voice


class ElevenLabsTTSService:
    """ElevenLabs TTS сервис для генерации высококачественной речи"""

    # Популярные голоса ElevenLabs
    VOICE_CONFIGS = {
        "rachel_en": {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (English)
            "name": "Rachel",
            "language": "en",
            "description": "Спокойный женский голос (английский)",
        },
        "adam_en": {
            "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam (English)
            "name": "Adam",
            "language": "en", 
            "description": "Глубокий мужской голос (английский)",
        },
        "domi_en": {
            "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Domi (English)
            "name": "Domi",
            "language": "en",
            "description": "Уверенный женский голос (английский)",
        },
        "elli_en": {
            "voice_id": "MF3mGyEYCl7XYWbV9V6O",  # Elli (English)
            "name": "Elli",
            "language": "en",
            "description": "Эмоциональный женский голос (английский)",
        },
    }

    def __init__(self, api_key: str, voice_id: str = "rachel_en"):
        """
        Инициализация ElevenLabs TTS сервиса
        
        Args:
            api_key: API ключ ElevenLabs
            voice_id: ID голоса или ключ из VOICE_CONFIGS
        """
        self.client = ElevenLabs(api_key=api_key)
        self.current_voice_id = self._resolve_voice_id(voice_id)
        self.model_id = "eleven_multilingual_v2"  # Поддерживает русский и английский
        
        # Параметры качества
        self.voice_settings = {
            "stability": 0.5,      # Стабильность голоса (0.0-1.0)
            "similarity_boost": 0.5, # Схожесть с оригиналом (0.0-1.0) 
            "style": 0.0,          # Стиль речи (0.0-1.0)
            "use_speaker_boost": True  # Усиление характеристик спикера
        }

    def _resolve_voice_id(self, voice_identifier: str) -> str:
        """Преобразует ключ голоса или возвращает voice_id как есть"""
        if voice_identifier in self.VOICE_CONFIGS:
            return self.VOICE_CONFIGS[voice_identifier]["voice_id"]
        return voice_identifier

    def get_available_voices(self) -> dict:
        """Возвращает список доступных предустановленных голосов"""
        return self.VOICE_CONFIGS

    def get_current_voice_info(self) -> dict:
        """Возвращает информацию о текущем голосе"""
        for key, config in self.VOICE_CONFIGS.items():
            if config["voice_id"] == self.current_voice_id:
                return {"key": key, **config}
        
        return {
            "key": "custom",
            "voice_id": self.current_voice_id,
            "name": "Custom Voice",
            "language": "unknown",
            "description": "Пользовательский голос",
        }

    def switch_voice(self, voice_identifier: str) -> bool:
        """
        Переключает на другой голос
        
        Args:
            voice_identifier: Ключ голоса из VOICE_CONFIGS или voice_id
            
        Returns:
            True если переключение успешно
        """
        try:
            new_voice_id = self._resolve_voice_id(voice_identifier)
            
            # Проверяем доступность голоса (опционально)
            # voices = self.client.voices.get_all()
            # available_voice_ids = [voice.voice_id for voice in voices.voices]
            # if new_voice_id not in available_voice_ids:
            #     return False
                
            self.current_voice_id = new_voice_id
            return True
        except Exception as e:
            print(f"❌ Ошибка переключения голоса: {e}")
            return False

    def set_voice_settings(
        self, 
        stability: Optional[float] = None, 
        similarity_boost: Optional[float] = None,
        style: Optional[float] = None,
        use_speaker_boost: Optional[bool] = None
    ):
        """
        Настройка параметров голоса
        
        Args:
            stability: Стабильность голоса (0.0-1.0)
            similarity_boost: Схожесть с оригиналом (0.0-1.0)
            style: Стиль речи (0.0-1.0)
            use_speaker_boost: Усиление характеристик спикера
        """
        if stability is not None:
            self.voice_settings["stability"] = max(0.0, min(1.0, stability))
        if similarity_boost is not None:
            self.voice_settings["similarity_boost"] = max(0.0, min(1.0, similarity_boost))
        if style is not None:
            self.voice_settings["style"] = max(0.0, min(1.0, style))
        if use_speaker_boost is not None:
            self.voice_settings["use_speaker_boost"] = use_speaker_boost

    def is_available(self) -> bool:
        """Проверяет доступность ElevenLabs TTS сервиса"""
        try:
            # Простая проверка - получаем информацию о пользователе
            user_info = self.client.user.get()
            print(f"🔍 ElevenLabs TTS: Пользователь найден, лимит символов: {getattr(user_info.subscription, 'character_limit', 'неизвестно')}")
            return True
        except Exception as e:
            print(f"🔍 ElevenLabs TTS проверка недоступна: {e}")
            if "401" in str(e) or "Unauthorized" in str(e):
                print("   💡 Ошибка аутентификации - проверьте ELEVENLABS_API_KEY")
            elif "403" in str(e) or "Forbidden" in str(e):
                print("   💡 Доступ запрещен - возможны географические ограничения")
            return False

    def _detect_language(self, text: str) -> str:
        """Автоопределение языка текста"""
        import re
        
        # Подсчет кириллических и латинских символов
        cyrillic_count = len(re.findall(r"[а-яёА-ЯЁ]", text))
        latin_count = len(re.findall(r"[a-zA-Z]", text))
        
        # Если больше кириллицы - русский, иначе английский
        if cyrillic_count > latin_count:
            return "ru"
        else:
            return "en"

    def text_to_audio_base64(self, text: str) -> str:
        """
        Конвертирует текст в аудио и возвращает в формате base64
        
        Args:
            text: Текст для озвучивания
            
        Returns:
            Base64 строка с аудио в формате MP3
        """
        if not text or not text.strip():
            raise ValueError("Текст не может быть пустым")

        try:
            print(f"🔤 ElevenLabs TTS: '{text[:50]}...'")
            
            # Генерируем аудио
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.current_voice_id,
                text=text.strip(),
                model_id=self.model_id,
                voice_settings=self.voice_settings,
            )

            # Собираем аудио данные
            audio_data = b"".join(audio_generator)
            
            # Кодируем в base64
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")
            
            print(f"✅ ElevenLabs TTS: Создано {len(audio_data)} байт аудио")
            return audio_b64

        except Exception as e:
            print(f"❌ Ошибка ElevenLabs TTS: {e}")
            raise Exception(f"Ошибка генерации аудио: {e}")

    def text_chunks_to_audio_stream(
        self, text_chunks: Generator[str, None, None]
    ) -> Generator[str, None, None]:
        """
        Конвертирует поток текстовых чанков в поток аудио (base64)
        
        Args:
            text_chunks: Генератор текстовых чанков
            
        Yields:
            Base64 строки с аудио
        """
        buffer = ""
        sentence_endings = [".", "!", "?", "\n"]
        min_length = 15  # Минимальная длина для озвучки (ElevenLabs лучше с длинными текстами)

        for chunk in text_chunks:
            buffer += chunk

            # Проверяем, есть ли завершенные предложения
            for ending in sentence_endings:
                if ending in buffer:
                    sentences = buffer.split(ending)
                    # Обрабатываем все завершенные предложения кроме последнего
                    for sentence in sentences[:-1]:
                        sentence = sentence.strip()
                        if sentence and len(sentence) >= min_length:
                            try:
                                audio_b64 = self.text_to_audio_base64(sentence)
                                yield audio_b64
                            except Exception as e:
                                print(f"❌ Ошибка генерации аудио для: {sentence[:50]}... - {e}")

                    # Оставляем незавершенную часть в буфере
                    buffer = sentences[-1]
                    break

        # Обрабатываем остаток, если есть
        if buffer.strip() and len(buffer.strip()) >= min_length:
            try:
                audio_b64 = self.text_to_audio_base64(buffer.strip())
                yield audio_b64
            except Exception as e:
                print(f"❌ Ошибка генерации аудио для остатка: {buffer[:50]}... - {e}")

    def get_voices_from_api(self) -> list:
        """
        Получает список всех доступных голосов из ElevenLabs API
        
        Returns:
            Список голосов с их характеристиками
        """
        try:
            voices_response = self.client.voices.get_all()
            voices_list = []
            
            for voice in voices_response.voices:
                voices_list.append({
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category if hasattr(voice, 'category') else 'unknown',
                    "description": voice.description if hasattr(voice, 'description') else '',
                    "labels": voice.labels if hasattr(voice, 'labels') else {}
                })
            
            return voices_list
        except Exception as e:
            print(f"❌ Ошибка получения голосов: {e}")
            return []

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
class BackwardCompatibleTTSService:
    """Сервис для обратной совместимости со старым API"""
    
    def __init__(self, elevenlabs_service: ElevenLabsTTSService):
        self.elevenlabs = elevenlabs_service

    def is_available(self) -> bool:
        return self.elevenlabs.is_available()

    def text_to_audio_base64(self, text: str) -> str:
        return self.elevenlabs.text_to_audio_base64(text)

    def text_chunks_to_audio_stream(
        self, text_chunks: Generator[str, None, None]
    ) -> Generator[str, None, None]:
        return self.elevenlabs.text_chunks_to_audio_stream(text_chunks)

    def get_available_models(self) -> dict:
        """Возвращает информацию о доступных голосах"""
        return self.elevenlabs.get_available_voices()

    def get_current_model_info(self) -> dict:
        """Возвращает информацию о текущем голосе"""
        return {
            "name": "elevenlabs_tts",
            "info": self.elevenlabs.get_current_voice_info(),
            "loaded": self.elevenlabs.is_available(),
        }

    def switch_model(self, voice_identifier: str) -> bool:
        """Переключает голос"""
        return self.elevenlabs.switch_voice(voice_identifier)