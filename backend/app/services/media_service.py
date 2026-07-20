import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from ..config import settings

class MediaService:
    @staticmethod
    async def build_final_movie(scenes_data, output_filename="final_story.mp4") -> str:
        # Chạy trong threadpool để tránh chặn event loop của FastAPI
        def process_media():
            final_clips = []
            output_path = os.path.join(settings.MEDIA_DIR, "output", output_filename)
            
            for scene in scenes_data:
                video_rel = scene.get("video_path")
                audio_rel = scene.get("audio_path")
                
                if not video_rel or not audio_rel:
                    continue
                
                # Chuyển đổi đường dẫn tĩnh tương đối thành đường dẫn tuyệt đối
                video_full_path = os.path.abspath(os.path.join(settings.STATIC_DIR, video_rel.lstrip("/")))
                audio_full_path = os.path.abspath(os.path.join(settings.STATIC_DIR, audio_rel.lstrip("/")))
                
                if not os.path.exists(video_full_path) or not os.path.exists(audio_full_path):
                    print(f"File missing: Video={video_full_path}, Audio={audio_full_path}")
                    continue
                    
                video_clip = VideoFileClip(video_full_path)
                audio_clip = AudioFileClip(audio_full_path)
                
                # Lấy độ dài tệp âm thanh
                duration = audio_clip.duration
                
                # Điều chỉnh thời lượng video theo tệp audio
                if video_clip.duration < duration:
                    video_clip = video_clip.set_duration(duration)
                else:
                    video_clip = video_clip.subclip(0, duration)
                    
                video_clip = video_clip.set_audio(audio_clip)
                final_clips.append(video_clip)
                
            if final_clips:
                final_video = concatenate_videoclips(final_clips, method="compose")
                final_video.write_videofile(
                    output_path, 
                    fps=24, 
                    codec="libx264", 
                    audio_codec="aac",
                    threads=4,
                    logger=None
                )
                
                # Giải phóng bộ nhớ
                for clip in final_clips:
                    try:
                        clip.close()
                    except Exception:
                        pass
                try:
                    final_video.close()
                except Exception:
                    pass
                
                return f"/media/output/{output_filename}"
            return ""
            
        return await asyncio.to_thread(process_media)
