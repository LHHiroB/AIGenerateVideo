import os
import asyncio
import httpx
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
        
        # 1. Thử dùng Kling AI
        if settings.KLING_API_KEY:
            try:
                print(f"Calling Kling AI for project {project_id} scene {scene_index}...")
                url = "https://api.klingai.com/v1/videos/generations"
                headers = {
                    "Authorization": f"Bearer {settings.KLING_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "kling-3.0",
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "duration": duration
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code in (200, 201):
                        res_data = response.json()
                        task_id = res_data.get("data", {}).get("task_id")
                        if task_id:
                            print(f"Kling task started: {task_id}. Polling...")
                            # Polling loop
                            for attempt in range(60): # 10 phút tối đa
                                await asyncio.sleep(10)
                                status_url = f"https://api.klingai.com/v1/tasks/{task_id}"
                                status_resp = await client.get(status_url, headers=headers)
                                if status_resp.status_code == 200:
                                    status_data = status_resp.json()
                                    task_status = status_data.get("data", {}).get("status")
                                    if task_status == "succeed":
                                        video_url = status_data.get("data", {}).get("result", {}).get("url")
                                        if video_url:
                                            # Tải video về local
                                            video_bytes = await client.get(video_url, timeout=60.0)
                                            def save_file():
                                                with open(filepath, "wb") as f:
                                                    f.write(video_bytes.content)
                                            await asyncio.to_thread(save_file)
                                            return f"/media/video/{filename}"
                                    elif task_status == "failed":
                                        print("Kling generation failed.")
                                        break
                            print("Kling polling timed out or failed.")
            except Exception as e:
                print(f"Failed to generate video via Kling AI: {e}")

        # 2. Thử dùng Runway AI
        elif settings.RUNWAY_API_KEY:
            try:
                print(f"Calling Runway AI for project {project_id} scene {scene_index}...")
                url = "https://api.runwayml.com/v1/tasks"
                headers = {
                    "Authorization": f"Bearer {settings.RUNWAY_API_KEY}",
                    "Content-Type": "application/json",
                    "X-Runway-Version": "2024-11-06"
                }
                payload = {
                    "taskType": "text_to_video",
                    "model": "gen3",
                    "promptText": prompt,
                    "ratio": "1280:720",
                    "duration": duration
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    if response.status_code in (200, 201):
                        res_data = response.json()
                        task_id = res_data.get("id")
                        if task_id:
                            print(f"Runway task started: {task_id}. Polling...")
                            for attempt in range(60):
                                await asyncio.sleep(10)
                                status_url = f"https://api.runwayml.com/v1/tasks/{task_id}"
                                status_resp = await client.get(status_url, headers=headers)
                                if status_resp.status_code == 200:
                                    status_data = status_resp.json()
                                    task_status = status_data.get("status")
                                    if task_status == "SUCCEEDED":
                                        video_url = status_data.get("output", [None])[0]
                                        if video_url:
                                            # Tải video về local
                                            video_bytes = await client.get(video_url, timeout=60.0)
                                            def save_file():
                                                with open(filepath, "wb") as f:
                                                    f.write(video_bytes.content)
                                            await asyncio.to_thread(save_file)
                                            return f"/media/video/{filename}"
                                    elif task_status == "FAILED":
                                        print("Runway generation failed.")
                                        break
                            print("Runway polling timed out or failed.")
            except Exception as e:
                print(f"Failed to generate video via Runway: {e}")

        # 3. Fallback sang vẽ ảnh và tạo video tĩnh Pillow + MoviePy
        print(f"Using local Pillow mockup for project {project_id} scene {scene_index}...")
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
            draw.text((80, height - 90), "LOCAL VISUAL GENERATOR", fill=(255, 255, 255), font=font)
            
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

