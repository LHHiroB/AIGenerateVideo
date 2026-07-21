import os
import asyncio
# pyrefly: ignore [missing-import]
from PIL import Image, ImageDraw, ImageFont
# pyrefly: ignore [missing-import]
from moviepy import ImageClip
from ..config import settings

class VideoService:
    @staticmethod
    async def generate_video(prompt: str, project_id: int, scene_index: int, duration: int) -> str:
        output_dir = os.path.join(settings.MEDIA_DIR, "video")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{project_id}_{scene_index}.mp4"
        filepath = os.path.join(output_dir, filename)
        
        def create_video_file():
            # 1. Tạo ảnh nền gradient đẹp
            width, height = 1280, 720
            # Màu nền xám/tối hiện đại
            image = Image.new("RGB", (width, height), color=(15, 23, 42)) # slate-900
            draw = ImageDraw.Draw(image)
            
            # Vẽ hình tròn phát sáng nhẹ ở trung tâm
            draw.ellipse([width//4, height//4, width*3//4, height*3//4], fill=(30, 41, 59)) # slate-800
            
            # Vẽ viền neon violet/indigo
            draw.rectangle([20, 20, width-20, height-20], outline=(99, 102, 241), width=4) # indigo-500
            
            # Cố gắng load font hệ thống
            try:
                # Trên Windows thường có Arial
                font = ImageFont.truetype("arial.ttf", 24)
                title_font = ImageFont.truetype("arial.ttf", 36)
            except Exception:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
                
            draw.text((60, 60), f"PROJECT #{project_id} - SCENE {scene_index}", fill=(129, 140, 248), font=title_font)
            
            # Wrap text prompt cho vừa màn hình
            wrapped_text = ""
            words = prompt.split()
            line = ""
            for word in words:
                if len(line + " " + word) < 70:
                    line += " " + word
                else:
                    wrapped_text += line + "\n"
                    line = word
            wrapped_text += line
            
            draw.text((60, 160), "Visual Prompt:", fill=(156, 163, 175), font=font)
            draw.text((60, 200), wrapped_text.strip(), fill=(243, 244, 246), font=font)
            
            # Vẽ nhãn AI Engine
            draw.rectangle([60, height - 100, 380, height - 50], fill=(79, 70, 229), outline=(129, 140, 248), width=2)
            draw.text((80, height - 90), "MOCK RUNWAY ENGINE v3", fill=(255, 255, 255), font=font)
            
            # Lưu ảnh tạm thời
            temp_image_path = os.path.join(output_dir, f"temp_{project_id}_{scene_index}.png")
            image.save(temp_image_path)
            
            # 2. Chuyển ảnh thành video clip với độ dài yêu cầu
            clip = ImageClip(temp_image_path).with_duration(duration)
            clip.write_videofile(filepath, fps=24, codec="libx264", logger=None)
            
            # Dọn dẹp ảnh tạm
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                
        # Chạy trong threadpool
        await asyncio.to_thread(create_video_file)
        return f"/media/video/{filename}"
