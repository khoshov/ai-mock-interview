import torch
from TTS.api import TTS


def download_silero():
    """Загружает и кэширует русскую модель Silero TTS."""
    print("📥 Загружаем и кэшируем модель Silero TTS (v4)...")
    try:
        torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            speaker="v4_ru",
            trust_repo=True,
        )
        print("✅ Silero TTS модель успешно закэширована!")
    except Exception as e:
        print(f"❌ Ошибка при кэшировании Silero: {e}")
        # Не прерываем сборку, если одна из моделей не скачалась


def download_xtts_v2():
    """Загружает и кэширует модель XTTS v2."""
    print("📥 Загружаем и кэшируем модель XTTS v2...")
    try:
        # Этот вызов скачает все необходимые файлы для модели
        TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("✅ XTTS v2 модель успешно закэширована!")
    except Exception as e:
        print(f"❌ Ошибка при кэшировании XTTS v2: {e}")


def download_whisper(model_name="tiny"):
    """Загружает и кэширует модель Whisper."""
    print(f"📥 Загружаем и кэшируем модель Whisper ({model_name})...")
    try:
        import whisper

        whisper.load_model(model_name)
        print(f"✅ Whisper модель ({model_name}) успешно закэширована!")
    except Exception as e:
        print(f"❌ Ошибка при кэшировании Whisper: {e}")
        raise e


if __name__ == "__main__":
    print("Начинаем предзагрузку моделей...")
    download_silero()
    download_xtts_v2()
    download_whisper()
    print("Предзагрузка моделей завершена.")
