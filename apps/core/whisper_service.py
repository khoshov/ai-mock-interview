
from openai import OpenAI
import os

class WhisperService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=self.api_key)

    def transcribe_audio(self, audio_file_path):
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
                return transcript.text
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

whisper_service = WhisperService()
