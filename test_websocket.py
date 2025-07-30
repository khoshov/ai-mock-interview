#!/usr/bin/env python3
"""
Скрипт для тестирования WebSocket с TTS
"""
import asyncio
import websockets
import json

async def test_websocket_tts():
    uri = "ws://localhost:8000/ws/interview/"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Подключен к WebSocket")
            
            # Отправляем сообщение с включенным TTS
            message = {
                "message": "Привет! Давай проведем тестовое интервью.",
                "enable_tts": True
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Отправлено:", message)
            
            # Слушаем ответы
            audio_chunks_received = 0
            text_chunks_received = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if 'audio_chunk' in data:
                        audio_chunks_received += 1
                        audio_size = len(data['audio_chunk'])
                        print(f"🔊 Получен аудио чанк #{audio_chunks_received}, размер: {audio_size}")
                        
                    elif 'answer_chunk' in data:
                        if data['answer_chunk'] == "END_OF_ANSWER":
                            print("✅ Получен конец ответа")
                            break
                        else:
                            text_chunks_received += 1
                            print(f"📝 Текст чанк #{text_chunks_received}: {data['answer_chunk'][:50]}...")
                            
                except asyncio.TimeoutError:
                    print("⏰ Таймаут ожидания ответа")
                    break
                    
            print(f"\n📊 Статистика:")
            print(f"   Текстовых чанков: {text_chunks_received}")
            print(f"   Аудио чанков: {audio_chunks_received}")
            
            if audio_chunks_received > 0:
                print("✅ TTS работает корректно!")
            else:
                print("❌ Аудио чанки не получены")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    print("🧪 Тестирование WebSocket с TTS...")
    asyncio.run(test_websocket_tts())