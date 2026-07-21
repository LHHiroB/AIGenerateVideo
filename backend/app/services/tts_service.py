import os
import asyncio
import httpx
# pyrefly: ignore [missing-import]
from gtts import gTTS
from ..config import settings

class TTSService:
    @staticmethod
    async def text_to_speech(text: str, project_id: int, scene_index: int) -> str:
        output_dir = os.path.join(settings.MEDIA_DIR, "audio")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{project_id}_{scene_index}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # 1. Thử dùng ElevenLabs nếu có API key
        if settings.ELEVENLABS_API_KEY:
            try:
                print(f"Calling ElevenLabs for project {project_id} scene {scene_index}...")
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
                headers = {
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        # Ghi nội dung nhị phân vào file
                        def write_binary():
                            with open(filepath, "wb") as f:
                                f.write(response.content)
                        await asyncio.to_thread(write_binary)
                        return f"/media/audio/{filename}"
                    else:
                        print(f"ElevenLabs API Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Failed to generate TTS via ElevenLabs: {e}")
                
        # 2. Fallback sang gTTS (Miễn phí) hoặc Mock
        print(f"Falling back to gTTS for project {project_id} scene {scene_index}...")
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
            # pyrefly: ignore [missing-import]
            from moviepy import AudioClip
            
            def make_fallback():
                make_frame = lambda t: np.sin(2 * np.pi * 440 * t)
                audio = AudioClip(make_frame, duration=5, fps=44100)
                audio.write_audiofile(filepath, fps=44100, logger=None)
                
            await asyncio.to_thread(make_fallback)
            
        return f"/media/audio/{filename}"

