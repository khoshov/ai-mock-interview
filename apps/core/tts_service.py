import torch
import torchaudio
import io
import base64
from typing import Generator, Dict, List
import os
from pathlib import Path

class MultiTTSService:
    """Универсальный TTS сервис поддерживающий несколько моделей"""
    
    AVAILABLE_MODELS = {
        'silero_ru': {
            'name': 'Silero Russian v4',
            'description': 'Быстрая русская модель',
            'type': 'silero',
            'language': 'ru',
            'speaker': 'baya'
        },
        'xtts_v2': {
            'name': 'XTTS v2 Multilingual',
            'description': 'Качественная многоязычная модель (авто-язык)',
            'type': 'xtts',
            'language': 'auto',  # Автоопределение языка
            'speaker': 'Claribel Dervla'
        },
        'xtts_v2_en': {
            'name': 'XTTS v2 English',
            'description': 'XTTS v2 только английский',
            'type': 'xtts',
            'language': 'en',
            'speaker': 'Claribel Dervla'
        },
        'xtts_v2_ru': {
            'name': 'XTTS v2 Russian',
            'description': 'XTTS v2 только русский',
            'type': 'xtts',
            'language': 'ru',
            'speaker': 'Claribel Dervla'
        }
    }
    
    def __init__(self, model_name: str = 'xtts_v2'):
        self.current_model_name = model_name
        self.model = None
        self.model_type = None
        self.sample_rate = 22050
        self.speaker = None
        self.language = 'ru'
        self._load_model()
        
    def _load_silero_model(self, config: Dict):
        """Загружает модель Silero TTS"""
        try:
            print(f"📥 Загружаем модель Silero TTS...")
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=config['language'],
                speaker='v4_ru',
                trust_repo=True
            )
            self.sample_rate = 48000
            self.speaker = config['speaker']
            self.model_type = 'silero'
            print("✅ Silero TTS модель успешно загружена!")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки Silero: {e}")
            return False
    
    def _load_xtts_model(self, config: Dict):
        """Загружает модель XTTS v2"""
        try:
            print(f"📥 Загружаем модель XTTS v2...")
            from TTS.api import TTS
            
            # Используем XTTS v2 модель
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            self.sample_rate = 22050
            self.speaker = config['speaker']
            self.language = config['language']
            self.model_type = 'xtts'
            print("✅ XTTS v2 модель успешно загружена!")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки XTTS v2: {e}")
            return False
        
    def _load_model(self):
        """Загружает выбранную модель TTS"""
        if self.current_model_name not in self.AVAILABLE_MODELS:
            print(f"❌ Неизвестная модель: {self.current_model_name}")
            self.current_model_name = 'xtts_v2'  # Fallback
            
        config = self.AVAILABLE_MODELS[self.current_model_name]
        
        if config['type'] == 'silero':
            success = self._load_silero_model(config)
        elif config['type'] == 'xtts':
            success = self._load_xtts_model(config)
        else:
            success = False
            
        if not success:
            print("❌ Не удалось загрузить основную модель, пробуем Silero как fallback...")
            self.current_model_name = 'silero_ru'
            self._load_silero_model(self.AVAILABLE_MODELS['silero_ru'])
    
    def switch_model(self, model_name: str) -> bool:
        """Переключает на другую модель"""
        if model_name == self.current_model_name:
            return True
            
        old_model = self.current_model_name
        self.current_model_name = model_name
        self.model = None
        
        self._load_model()
        
        if self.model is None:
            # Возвращаемся к предыдущей модели
            self.current_model_name = old_model
            self._load_model()
            return False
            
        return True
    
    def get_available_models(self) -> Dict:
        """Возвращает список доступных моделей"""
        return self.AVAILABLE_MODELS
    
    def get_current_model_info(self) -> Dict:
        """Возвращает информацию о текущей модели"""
        return {
            'name': self.current_model_name,
            'info': self.AVAILABLE_MODELS.get(self.current_model_name, {}),
            'loaded': self.model is not None
        }
            
    def is_available(self) -> bool:
        """Проверяет доступность TTS сервиса"""
        return self.model is not None
        
    def text_to_audio_base64(self, text: str) -> str:
        """
        Конвертирует текст в аудио и возвращает в формате base64
        """
        if not self.is_available():
            raise Exception("TTS сервис недоступен")
            
        try:
            if self.model_type == 'silero':
                return self._silero_text_to_audio_base64(text)
            elif self.model_type == 'xtts':
                return self._xtts_text_to_audio_base64(text)
            else:
                raise Exception("Неизвестный тип модели")
                
        except Exception as e:
            print(f"❌ Ошибка генерации аудио: {e}")
            raise
    
    def _silero_text_to_audio_base64(self, text: str) -> str:
        """Генерация аудио через Silero"""
        audio = self.model.apply_tts(
            text=text,
            speaker=self.speaker,
            sample_rate=self.sample_rate
        )
        
        # Конвертируем в байты
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio.unsqueeze(0), self.sample_rate, format='wav')
        buffer.seek(0)
        
        # Кодируем в base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _detect_language(self, text: str) -> str:
        """Автоопределение языка текста"""
        # Простая эвристика для определения языка
        import re
        
        # Подсчет кириллических и латинских символов
        cyrillic_count = len(re.findall(r'[а-яёА-ЯЁ]', text))
        latin_count = len(re.findall(r'[a-zA-Z]', text))
        
        # Если есть и русские, и английские символы - используем русский (он лучше справляется со смешанным текстом)
        if cyrillic_count > 0:
            return 'ru'
        elif latin_count > 0:
            return 'en'
        else:
            return 'ru'  # По умолчанию русский
    
    def _xtts_text_to_audio_base64(self, text: str) -> str:
        """Генерация аудио через XTTS v2"""
        import tempfile
        import numpy as np
        
        # Автоопределение языка
        detected_language = self._detect_language(text)
        
        print(f"🔤 Текст: '{text[:50]}...' | Язык: {detected_language}")
        
        # Создаем временный файл для аудио
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Определяем язык для генерации
            if self.language == 'auto':
                target_language = detected_language
            else:
                target_language = self.language
            
            print(f"🎯 Используем язык: {target_language}")
            
            # Генерируем аудио в файл
            self.model.tts_to_file(
                text=text,
                file_path=tmp_path,
                speaker=self.speaker,
                language=target_language
            )
            
            # Читаем файл и конвертируем в base64
            with open(tmp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
                return base64.b64encode(audio_data).decode('utf-8')
                
        finally:
            # Удаляем временный файл
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    def text_chunks_to_audio_stream(self, text_chunks: Generator[str, None, None]) -> Generator[str, None, None]:
        """
        Конвертирует поток текстовых чанков в поток аудио (base64)
        """
        buffer = ""
        sentence_endings = ['.', '!', '?', '\n']
        
        for chunk in text_chunks:
            buffer += chunk
            
            # Проверяем, есть ли завершенные предложения
            for ending in sentence_endings:
                if ending in buffer:
                    sentences = buffer.split(ending)
                    # Обрабатываем все завершенные предложения кроме последнего
                    for sentence in sentences[:-1]:
                        sentence = sentence.strip()
                        if sentence and len(sentence) > 10:  # Минимальная длина для озвучки
                            try:
                                audio_b64 = self.text_to_audio_base64(sentence)
                                yield audio_b64
                            except Exception as e:
                                print(f"❌ Ошибка генерации аудио для: {sentence[:50]}... - {e}")
                    
                    # Оставляем незавершенную часть в буфере
                    buffer = sentences[-1]
                    break
        
        # Обрабатываем остаток, если есть
        if buffer.strip() and len(buffer.strip()) > 10:
            try:
                audio_b64 = self.text_to_audio_base64(buffer.strip())
                yield audio_b64
            except Exception as e:
                print(f"❌ Ошибка генерации аудио для остатка: {buffer[:50]}... - {e}")


# Создаем глобальный экземпляр сервиса
tts_service = MultiTTSService()