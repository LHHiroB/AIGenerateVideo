from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(String, default="draft") # draft, generating, pending_review, completed
    global_art_style = Column(Text, nullable=True)
    character_presets = Column(Text, nullable=True) # Lưu dưới dạng JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    scene_index = Column(Integer)
    narration = Column(Text)
    visual_prompt = Column(Text)
    character_focus = Column(String, default="none")
    audio_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    status = Column(String, default="pending") # pending, processing, success, failed
    estimated_duration = Column(Integer, default=5)

    project = relationship("Project", back_populates="scenes")
