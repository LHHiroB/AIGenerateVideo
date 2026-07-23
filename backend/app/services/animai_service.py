import os
import base64
import asyncio
import httpx
from typing import Optional, Dict, Any
from ..config import settings

class AnimAIService:
    @staticmethod
    def get_headers() -> Dict[str, str]:
        api_key = settings.ANIMAI_API_KEY.strip()
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @staticmethod
    async def poll_job(client: httpx.AsyncClient, job_id: str, timeout_seconds: int = 600) -> Dict[str, Any]:
        url = f"{settings.ANIMAI_BASE_URL.rstrip('/')}/api/v1/internal/jobs/get"
        headers = AnimAIService.get_headers()
        payload = {"job_id": job_id}
        
        elapsed = 0
        poll_interval = 5
        
        while elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            try:
                res = await client.post(url, headers=headers, json=payload, timeout=30.0)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        result = data.get("result", {})
                        status = result.get("status")
                        if status == "completed":
                            return result
                        elif status == "failed":
                            err_msg = result.get("error_message", "AnimAI Job failed")
                            raise Exception(f"Job failed: {err_msg}")
                        elif status == "canceled":
                            raise Exception("Job was canceled")
            except Exception as e:
                print(f"[AnimAI Poll Warning] {e}")
                
        raise TimeoutError(f"AnimAI Job {job_id} timed out after {timeout_seconds}s")

    @staticmethod
    async def download_file(client: httpx.AsyncClient, download_url: str, save_path: str):
        headers = {}
        if not download_url.startswith("http"):
            download_url = f"{settings.ANIMAI_BASE_URL.rstrip('/')}{download_url}"
            headers["Authorization"] = f"Bearer {settings.ANIMAI_API_KEY.strip()}"

        res = await client.get(download_url, headers=headers, follow_redirects=True, timeout=60.0)
        if res.status_code == 200:
            def save_bytes():
                with open(save_path, "wb") as f:
                    f.write(res.content)
            await asyncio.to_thread(save_bytes)
        else:
            raise Exception(f"Failed to download media file: Status {res.status_code}")

    @staticmethod
    async def generate_image(prompt: str, save_path: str, aspect_ratio: str = "16:9") -> str:
        """Tạo ảnh qua AnimAI Studio API và lưu về disk"""
        url = f"{settings.ANIMAI_BASE_URL.rstrip('/')}/api/v1/internal/images/generate"
        headers = AnimAIService.get_headers()
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "model": "qwen-image",
            "count": 1
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code not in (200, 201):
                raise Exception(f"AnimAI Image request failed ({res.status_code}): {res.text}")
                
            data = res.json()
            if not data.get("ok"):
                raise Exception(f"AnimAI Image error: {data.get('error')}")
                
            job_id = data.get("result", {}).get("job_id")
            print(f"[AnimAI] Image job created: {job_id}. Polling...")
            
            job_result = await AnimAIService.poll_job(client, job_id)
            results = job_result.get("results", [])
            if not results:
                raise Exception("AnimAI Image completed but returned no results")
                
            media = results[0]
            dl_url = media.get("download_url") or media.get("url")
            await AnimAIService.download_file(client, dl_url, save_path)
            return save_path

    @staticmethod
    async def generate_video_from_image(prompt: str, image_path: str, save_path: str, duration: int = 5) -> str:
        """Tạo Video từ ảnh (Image-to-Video) qua AnimAI Studio API"""
        def read_img_base64():
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(image_path)[1].lstrip(".").lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                return f"data:{mime};base64,{encoded}"
                
        base64_data = await asyncio.to_thread(read_img_base64)
        
        url = f"{settings.ANIMAI_BASE_URL.rstrip('/')}/api/v1/internal/videos/generate"
        headers = AnimAIService.get_headers()
        payload = {
            "prompt": prompt,
            "source_mode": "start_image",
            "resolution": "720P",
            "aspect_ratio": "16:9",
            "duration_seconds": duration,
            "profile": "gen_01",
            "image": {
                "filename": os.path.basename(image_path),
                "data": base64_data
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code not in (200, 201):
                raise Exception(f"AnimAI Video request failed ({res.status_code}): {res.text}")
                
            data = res.json()
            if not data.get("ok"):
                raise Exception(f"AnimAI Video error: {data.get('error')}")
                
            job_id = data.get("result", {}).get("job_id")
            print(f"[AnimAI] Video job created: {job_id}. Polling...")
            
            job_result = await AnimAIService.poll_job(client, job_id, timeout_seconds=900)
            results = job_result.get("results", [])
            if not results:
                raise Exception("AnimAI Video completed but returned no results")
                
            media = results[0]
            dl_url = media.get("download_url") or media.get("url")
            await AnimAIService.download_file(client, dl_url, save_path)
            return save_path
