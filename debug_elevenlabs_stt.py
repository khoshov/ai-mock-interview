#!/usr/bin/env python3
"""
Отладочная утилита для ElevenLabs STT API
"""

import os
import sys
from pathlib import Path

# Добавляем путь к Django проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from config.settings import ELEVENLABS_API_KEY
from elevenlabs import ElevenLabs


def debug_stt_api():
    """Отладка STT API"""
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY не найден")
        return
        
    print("🔍 Отладка ElevenLabs STT API")
    print("=" * 40)
    
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Проверяем наличие speech_to_text
        if not hasattr(client, 'speech_to_text'):
            print("❌ client.speech_to_text не найден")
            print("🔍 Доступные атрибуты client:")
            for attr in dir(client):
                if not attr.startswith('_'):
                    print(f"   - {attr}")
            return
            
        stt_client = client.speech_to_text
        print("✅ client.speech_to_text найден")
        
        # Смотрим методы
        print("🔍 Методы speech_to_text:")
        for attr in dir(stt_client):
            if not attr.startswith('_'):
                method = getattr(stt_client, attr)
                if callable(method):
                    print(f"   - {attr}()")
                else:
                    print(f"   - {attr}")
        
        # Смотрим convert метод детально
        if hasattr(stt_client, 'convert'):
            print("\n🔍 Анализ метода convert:")
            convert_method = stt_client.convert
            
            # Получаем документацию
            if hasattr(convert_method, '__doc__') and convert_method.__doc__:
                print(f"📖 Документация:\n{convert_method.__doc__}")
            
            # Получаем сигнатуру
            try:
                import inspect
                sig = inspect.signature(convert_method)
                print(f"📝 Сигнатура: {sig}")
                
                print("📋 Параметры:")
                for name, param in sig.parameters.items():
                    default = param.default if param.default != inspect.Parameter.empty else "нет"
                    annotation = param.annotation if param.annotation != inspect.Parameter.empty else "нет"
                    print(f"   - {name}: {annotation} = {default}")
                    
            except Exception as e:
                print(f"❌ Ошибка получения сигнатуры: {e}")
        
        print("\n🧪 Пробуем минимальные вызовы...")
        
        # Тестируем различные варианты вызова
        import tempfile
        import wave
        
        # Создаем тестовый аудио файл
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                silence = b'\x00\x00' * 8000  # 0.5 секунды тишины
                wav_file.writeframes(silence)
            
            temp_file_path = temp_file.name
        
        try:
            # Тест 1: только file
            print("🧪 Тест 1: convert(file=...)")
            try:
                with open(temp_file_path, "rb") as audio_file:
                    result = stt_client.convert(file=audio_file)
                    print(f"✅ Успех! Тип результата: {type(result)}")
                    if hasattr(result, 'text'):
                        print(f"   Текст: '{result.text}'")
                    print(f"   Все атрибуты: {dir(result)}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест 2: с правильными model_id
            print("\n🧪 Тест 2: convert с правильными моделями...")
            
            models_to_test = ["scribe_v1", "scribe_v1_experimental"]
            
            for model_id in models_to_test:
                print(f"   🧪 Тестируем модель: {model_id}")
                try:
                    with open(temp_file_path, "rb") as audio_file:
                        result = stt_client.convert(file=audio_file, model_id=model_id)
                        print(f"   ✅ Модель {model_id} работает!")
                        if hasattr(result, 'text'):
                            print(f"      Текст: '{result.text}'")
                        break  # Если одна модель работает, не тестируем остальные
                except Exception as e:
                    print(f"   ❌ Модель {model_id} не работает: {e}")
                    if "invalid_model_id" in str(e):
                        print(f"      💡 {model_id} не поддерживается")
            
            # Тест 3: другие возможные параметры
            print("\n🧪 Тест 3: convert с другими параметрами...")
            try:
                with open(temp_file_path, "rb") as audio_file:
                    # Пробуем другие варианты параметров
                    if 'audio' in str(inspect.signature(stt_client.convert)):
                        print("   Пробуем параметр 'audio'...")
                        result = stt_client.convert(audio=audio_file.read())
                    elif 'data' in str(inspect.signature(stt_client.convert)):
                        print("   Пробуем параметр 'data'...")
                        result = stt_client.convert(data=audio_file.read())
                    else:
                        print("   Нет альтернативных параметров")
                        
            except Exception as e:
                print(f"❌ Ошибка альтернативных параметров: {e}")
                
        finally:
            import os
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")


if __name__ == "__main__":
    debug_stt_api()