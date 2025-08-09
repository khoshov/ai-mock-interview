import whisper


class LocalWhisperService:
    def __init__(self, model_name="tiny"):
        print(f"📥 Загружаем локальную модель Whisper: {model_name}")
        try:
            self.model = whisper.load_model(model_name)
            print(f"✅ Модель Whisper ({model_name}) успешно загружена.")
        except Exception as e:
            print(f"❌ Ошибка загрузки модели Whisper: {e}")
            self.model = None

    def transcribe_audio(self, audio_file_path):
        if not self.model:
            print("❌ Модель Whisper не загружена, транскрибация невозможна.")
            return None

        try:
            print(f"🎤 Транскрибируем аудио: {audio_file_path}")
            result = self.model.transcribe(audio_file_path)
            print(f"💬 Результат: {result['text']}")
            return result["text"]
        except Exception as e:
            print(f"❌ Ошибка во время транскрибации: {e}")
            return None


# Создаем экземпляр сервиса с моделью 'tiny'
whisper_service = LocalWhisperService(model_name="tiny")
