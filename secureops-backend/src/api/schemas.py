from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class UploadResponse(BaseModel):
    video_id: str
    status: str
    filename: Optional[str] = None


class StatusResponse(BaseModel):
    video_id: str
    status: str


class SummaryResponse(BaseModel):
    pipeline_status: str              # PASS | FAIL | PENDING
    accuracy: float                   # 0.0–1.0
    pass_threshold: float             # e.g. 0.7
    total_samples: int
    integrity_hash: Optional[str]
    dataset: Optional[str]
    timestamp: Optional[datetime]
    violations: Dict[str, int]


class Violation(BaseModel):
    file_name: str
    type: str # violation_type
    severity: str
    confidence: Optional[float]
    timestamp: Optional[datetime]
    image_path: Optional[str] = None # Added for visual evidence


class ProximityEvent(BaseModel):
    worker_id: Optional[str]
    machine: str # machine_type
    distance_px: float
    risk: str # risk_level
    timestamp: Optional[datetime]
    image_path: Optional[str] = None # Added for visual evidence


class AnalysisResult(BaseModel):
    """Schema for analysis result."""
    total_detections: int
    persons: int
    ppe_violations: int
    processing_time: float
    detections: List[Dict[str, Any]]


# --- AUTH SCHEMAS ---

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: str = "viewer" # default

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    id: UUID
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
