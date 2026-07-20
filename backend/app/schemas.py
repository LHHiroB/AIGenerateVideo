from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

# --- Pydantic Schemas for LLM Structured Output ---
class LLMScene(BaseModel):
    scene_index: int
    narration: str
    character_focus: str
    visual_prompt: str
    estimated_duration: int

class LLMStoryOutput(BaseModel):
    story_title: str
    global_art_style: str
    character_presets: Dict[str, str]
    scenes: List[LLMScene]

# --- Pydantic Schemas for FastAPI Request/Response ---
class ProjectCreate(BaseModel):
    title: str

class SceneUpdatePrompt(BaseModel):
    visual_prompt: str

class SceneResponse(BaseModel):
    id: int
    project_id: int
    scene_index: int
    narration: str
    visual_prompt: str
    character_focus: str
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    status: str
    estimated_duration: int

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: int
    title: str
    status: str
    global_art_style: Optional[str] = None
    character_presets: Optional[str] = None
    created_at: datetime
    scenes: List[SceneResponse] = []

    class Config:
        from_attributes = True
