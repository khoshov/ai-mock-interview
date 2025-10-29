#!/usr/bin/env python3
"""
Утилита для тестирования ElevenLabs API ключа
Использование: python test_elevenlabs_api.py
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


def test_api_key():
    """Тестирует ElevenLabs API ключ"""
    
    print("🔧 Тестирование ElevenLabs API ключа...")
    print("=" * 50)
    
    # Проверяем наличие ключа
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY не найден в переменных окружения")
        print("   Добавьте ELEVENLABS_API_KEY=your_api_key в файл .env")
        return False
    
    print(f"🔑 API ключ найден (длина: {len(ELEVENLABS_API_KEY)} символов)")
    print(f"   Первые символы: {ELEVENLABS_API_KEY[:8]}...")
    
    # Создаем клиент
    try:
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("✅ ElevenLabs клиент создан")
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        return False
    
    # Тестируем доступ к API
    try:
        print("🔍 Проверяем доступ к API...")
        user_info = client.user.get()
        print("✅ Успешно подключились к ElevenLabs API")
        
        # Выводим информацию о пользователе
        if hasattr(user_info, 'subscription'):
            subscription = user_info.subscription
            print(f"📊 Информация о подписке:")
            print(f"   - Лимит символов: {getattr(subscription, 'character_limit', 'неизвестно')}")
            print(f"   - Использовано символов: {getattr(subscription, 'character_count', 'неизвестно')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка доступа к API: {e}")
        
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print("   💡 Ошибка аутентификации:")
            print("      - Проверьте правильность API ключа")
            print("      - Убедитесь что ключ активен")
            print("      - Получить новый ключ: https://elevenlabs.io/")
        elif "403" in error_str or "Forbidden" in error_str:
            print("   💡 Доступ запрещен:")
            print("      - Возможны географические ограничения")
            print("      - Попробуйте использовать VPN")
            print("      - Проверьте права доступа аккаунта")
        else:
            print("   💡 Неизвестная ошибка - проверьте подключение к интернету")
            
        return False


def test_voices():
    """Тестирует получение списка голосов"""
    
    if not ELEVENLABS_API_KEY:
        return False
        
    try:
        print("\n🎤 Тестируем получение голосов...")
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        voices = client.voices.get_all()
        print(f"✅ Найдено {len(voices.voices)} голосов")
        
        print("📋 Доступные голоса:")
        for voice in voices.voices[:5]:  # Показываем первые 5
            print(f"   - {voice.name} (ID: {voice.voice_id})")
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка получения голосов: {e}")
        return False


def test_stt_api():
    """Тестирует STT API методы"""
    
    if not ELEVENLABS_API_KEY:
        return False
        
    try:
        print("\n🔍 Проверяем доступные STT методы...")
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Проверяем наличие speech_to_text атрибута
        if hasattr(client, 'speech_to_text'):
            print("✅ client.speech_to_text доступен")
            
            # Проверяем методы
            stt_client = client.speech_to_text
            print(f"📋 Доступные методы STT:")
            for attr in dir(stt_client):
                if not attr.startswith('_'):
                    print(f"   - {attr}")
                    
            # Проверяем метод convert
            if hasattr(stt_client, 'convert'):
                print("✅ Метод convert найден")
                
                # Попробуем посмотреть сигнатуру метода
                import inspect
                try:
                    sig = inspect.signature(stt_client.convert)
                    print(f"📝 Сигнатура convert: {sig}")
                    
                    # Покажем список параметров
                    params = list(sig.parameters.keys())
                    print(f"📋 Параметры convert: {params}")
                except:
                    print("📝 Не удалось получить сигнатуру convert")
                    
                # Попробуем создать тестовый аудио файл и протестировать API
                try:
                    print("🧪 Тестируем минимальный вызов STT...")
                    import tempfile
                    import wave
                    
                    # Создаем минимальный WAV файл для теста
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        # Создаем простой WAV файл с тишиной
                        with wave.open(temp_file.name, 'wb') as wav_file:
                            wav_file.setnchannels(1)  # моно
                            wav_file.setsampwidth(2)  # 16 бит
                            wav_file.setframerate(16000)  # 16kHz
                            # Записываем 1 секунду тишины
                            silence = b'\x00\x00' * 16000
                            wav_file.writeframes(silence)
                        
                        temp_file_path = temp_file.name
                    
                    try:
                        with open(temp_file_path, "rb") as audio_file:
                            result = stt_client.convert(file=audio_file)
                            print(f"✅ Тест STT прошел успешно: {type(result)}")
                            if hasattr(result, 'text'):
                                print(f"📝 Результат: '{result.text}'")
                    finally:
                        import os
                        os.unlink(temp_file_path)
                        
                except Exception as test_e:
                    print(f"🧪 Тест STT не прошел: {test_e}")
                    if "unexpected keyword argument" in str(test_e):
                        print("   💡 Проблема с параметрами API - возможно изменился интерфейс")
            else:
                print("❌ Метод convert не найден")
        else:
            print("❌ client.speech_to_text недоступен")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки STT API: {e}")
        return False


def main():
    """Основная функция"""
    
    print("🧪 ElevenLabs API Тестер")
    print("=" * 50)
    
    # Тестируем API ключ
    api_test = test_api_key()
    
    if api_test:
        # Тестируем голоса
        voices_test = test_voices()
        
        # Тестируем STT API
        stt_test = test_stt_api()
        
        if voices_test and stt_test:
            print("\n✅ Все тесты пройдены успешно!")
            print("   ElevenLabs API готов к использованию")
        else:
            print("\n⚠️ Некоторые тесты не пройдены")
            if not voices_test:
                print("   - Проблемы с TTS/голосами")
            if not stt_test:
                print("   - Проблемы с STT")
    else:
        print("\n❌ Тесты не пройдены")
        print("   Исправьте ошибки конфигурации")
        
    print("=" * 50)


if __name__ == "__main__":
    main()