import os
import json
import asyncio
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .config import settings
from .database import engine, Base, get_db
from . import models, schemas
from .services.llm_service import LLMService
from .services.tts_service import TTSService
from .services.video_service import VideoService
from .services.media_service import MediaService

# Tạo bảng trong SQLite
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Video Generator Backend", version="1.0.0")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper để cập nhật trạng thái phân cảnh và project chạy ngầm
async def generate_scene_assets_task(project_id: int, db_session_factory):
    # Sử dụng db_session_factory để tạo session độc lập chạy ngầm
    db: Session = db_session_factory()
    try:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            return
            
        project.status = "generating"
        db.commit()

        # Tạo đồng thời tất cả các cảnh
        tasks = []
        for scene in project.scenes:
            # Gộp prompt đầy đủ từ: global_art_style + character_preset + visual_prompt
            char_presets = json.loads(project.character_presets or "{}")
            preset_prompt = char_presets.get(scene.character_focus, "")
            
            full_visual_prompt = f"{project.global_art_style}. "
            if preset_prompt:
                full_visual_prompt += f"{preset_prompt}. "
            full_visual_prompt += scene.visual_prompt
            
            # Hàm sinh đơn lẻ từng cảnh
            tasks.append(process_single_scene(scene.id, full_visual_prompt, scene.narration, scene.estimated_duration, db_session_factory))
            
        await asyncio.gather(*tasks)
        
        # Cập nhật trạng thái project
        project.status = "pending_review"
        db.commit()
    except Exception as e:
        print(f"Background Job Error: {e}")
        if project:
            project.status = "draft"
            db.commit()
    finally:
        db.close()

async def process_single_scene(scene_id: int, full_prompt: str, narration: str, duration: int, db_session_factory):
    db: Session = db_session_factory()
    try:
        scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
        if not scene:
            return
            
        scene.status = "processing"
        db.commit()
        
        # Chạy đồng thời TTS (Audio) và Video generation cho scene này
        audio_task = TTSService.text_to_speech(narration, scene.project_id, scene.scene_index)
        video_task = VideoService.generate_video(full_prompt, scene.project_id, scene.scene_index, duration)
        
        audio_path, video_path = await asyncio.gather(audio_task, video_task)
        
        scene.audio_path = audio_path
        scene.video_path = video_path
        scene.status = "success"
        db.commit()
    except Exception as e:
        print(f"Scene {scene_id} generation failed: {e}")
        scene.status = "failed"
        db.commit()
    finally:
        db.close()

async def regenerate_single_scene_task(scene_id: int, full_prompt: str, duration: int, db_session_factory):
    db: Session = db_session_factory()
    try:
        scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
        if not scene:
            return
            
        scene.status = "processing"
        db.commit()
        
        # Chỉ tạo lại video cho phân cảnh này
        video_path = await VideoService.generate_video(full_prompt, scene.project_id, scene.scene_index, duration)
        
        scene.video_path = video_path
        scene.status = "success"
        db.commit()
    except Exception as e:
        print(f"Regenerate Scene {scene_id} failed: {e}")
        scene.status = "failed"
        db.commit()
    finally:
        db.close()


# --- API Endpoints ---

@app.post("/api/projects", response_model=schemas.ProjectResponse)
async def create_project(payload: schemas.ProjectCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Gọi LLM sinh kịch bản cấu trúc từ tiêu đề
    try:
        story = await LLMService.generate_story(payload.title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM failed: {str(e)}")
        
    # 2. Lưu thông tin Project
    db_project = models.Project(
        title=story.story_title,
        status="draft",
        global_art_style=story.global_art_style,
        character_presets=json.dumps(story.character_presets)
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # 3. Lưu danh sách phân cảnh Scenes
    for scene in story.scenes:
        db_scene = models.Scene(
            project_id=db_project.id,
            scene_index=scene.scene_index,
            narration=scene.narration,
            visual_prompt=scene.visual_prompt,
            character_focus=scene.character_focus,
            estimated_duration=scene.estimated_duration,
            status="pending"
        )
        db.add(db_scene)
    db.commit()
    db.refresh(db_project)
    
    # 4. Kích hoạt background task để sinh Audio & Video song song
    from .database import SessionLocal
    background_tasks.add_task(generate_scene_assets_task, db_project.id, SessionLocal)
    
    return db_project

@app.get("/api/projects", response_model=List[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.created_at.desc()).all()

@app.get("/api/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/api/scenes/{scene_id}/regenerate", response_model=schemas.SceneResponse)
async def regenerate_scene(scene_id: int, payload: schemas.SceneUpdatePrompt, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    scene = db.query(models.Scene).filter(models.Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
        
    project = scene.project
    
    # Cập nhật prompt hình ảnh mới người dùng sửa đổi vào DB
    scene.visual_prompt = payload.visual_prompt
    scene.status = "processing"
    db.commit()
    db.refresh(scene)
    
    # Gộp prompt mới
    char_presets = json.loads(project.character_presets or "{}")
    preset_prompt = char_presets.get(scene.character_focus, "")
    full_visual_prompt = f"{project.global_art_style}. "
    if preset_prompt:
        full_visual_prompt += f"{preset_prompt}. "
    full_visual_prompt += scene.visual_prompt
    
    # Kích hoạt background task tạo lại video
    from .database import SessionLocal
    background_tasks.add_task(regenerate_single_scene_task, scene.id, full_visual_prompt, scene.estimated_duration, SessionLocal)
    
    return scene

@app.post("/api/projects/{project_id}/merge")
async def merge_project_video(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Chuẩn bị dữ liệu cho module media
    scenes_data = []
    for s in sorted(project.scenes, key=lambda x: x.scene_index):
        if s.status != "success":
            raise HTTPException(status_code=400, detail=f"Scene {s.scene_index} chưa sẵn sàng (Trạng thái: {s.status})")
        scenes_data.append({
            "video_path": s.video_path,
            "audio_path": s.audio_path
        })
        
    try:
        output_filename = f"project_{project.id}_final.mp4"
        final_video_url = await MediaService.build_final_movie(scenes_data, output_filename)
        
        if final_video_url:
            project.status = "completed"
            db.commit()
            return {"status": "success", "final_video_url": final_video_url}
        else:
            raise HTTPException(status_code=500, detail="Merge video thất bại")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Xảy ra lỗi khi ghép video: {str(e)}")


# Serve file media được tạo ra
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# Serve Frontend Tĩnh (Đặt ở cuối cùng để tránh chặn các API router)
app.mount("/", StaticFiles(directory=settings.STATIC_DIR, html=True), name="frontend")
