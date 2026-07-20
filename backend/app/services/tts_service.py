import os
import asyncio
from gtts import gTTS
from ..config import settings

class TTSService:
    @staticmethod
    async def text_to_speech(text: str, project_id: int, scene_index: int) -> str:
        output_dir = os.path.join(settings.MEDIA_DIR, "audio")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{project_id}_{scene_index}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        try:
            # Chạy gTTS trong threadpool để tránh chặn event loop
            def generate_speech():
                tts = gTTS(text=text, lang='vi')
                tts.save(filepath)
            
            await asyncio.to_thread(generate_speech)
        except Exception as e:
            print(f"TTS Error: {e}, falling back to generating mock audio via moviepy")
            # Fallback sang tạo clip âm thanh tĩnh nếu mất mạng hoặc lỗi
            import numpy as np
            from moviepy.audio.AudioClip import AudioClip
            
            def make_fallback():
                make_frame = lambda t: np.sin(2 * np.pi * 440 * t)
                audio = AudioClip(make_frame, duration=5, fps=44100)
                audio.write_audiofile(filepath, fps=44100, logger=None)
                
            await asyncio.to_thread(make_fallback)
            
        return f"/media/audio/{filename}"
