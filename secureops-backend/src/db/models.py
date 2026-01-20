"""Database models for SecureOps platform."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()


class Detection(Base):
    """YOLO detection results."""
    __tablename__ = "detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(String, nullable=False, index=True)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Detection details
    class_id = Column(Integer, nullable=False)
    class_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Bounding box (x1, y1, x2, y2)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index('idx_detections_video_frame', 'video_id', 'frame_number'),
        Index('idx_detections_class', 'class_name'),
        Index('idx_detections_timestamp', 'timestamp'),
    )



# --- AUTHORITATIVE SCHEMA MODELS ---

class Upload(Base):
    """Track uploaded jobs (images / PDF)."""
    __tablename__ = "uploads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_type = Column(String, nullable=False) # 'image', 'video', 'pdf'
    original_filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending") 
    # pending, processing, generating_output, completed, failed
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_uploads_status', 'status'),
        Index('idx_uploads_created_at', 'created_at'),
    )


class SafetyViolation(Base):
    """PPE, Zone, and Time-based violations."""
    __tablename__ = "safety_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), nullable=False, index=True) # Linked to Upload
    
    file_name = Column(String, nullable=False)
    violation_type = Column(String, nullable=False) # 'PPE', 'ZONE', 'TIME_BASED'
    severity = Column(String, nullable=False) # 'LOW', 'MEDIUM', 'HIGH'
    
    confidence = Column(Float, nullable=True)
    frame_number = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Metadata for advanced reporting (bboxes, track IDs, rules)
    extra_metadata = Column(JSON, nullable=True)
    image_path = Column(String, nullable=True) # Evidence image path

    __table_args__ = (
        Index('idx_violations_type', 'violation_type'),
        Index('idx_violations_detected_at', 'detected_at'),
    )


class ProximityEvent(Base):
    """Worker–machine distance risks."""
    __tablename__ = "proximity_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), nullable=False, index=True) # Linked to Upload
    
    worker_id = Column(String, nullable=True)
    machine_type = Column(String, nullable=False)
    distance_px = Column(Float, nullable=False)
    
    risk_level = Column(String, nullable=False) # 'LOW', 'MEDIUM', 'HIGH'
    
    frame_number = Column(Integer, nullable=True)
    image_path = Column(String, nullable=True) # Evidence image path
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_proximity_risk_level', 'risk_level'),
        Index('idx_proximity_detected_at', 'detected_at'),
    )


class SiteMetrics(Base):
    """Aggregated run-level metrics."""
    __tablename__ = "site_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_id = Column(UUID(as_uuid=True), nullable=False, index=True) # Linked to Upload
    
    total_files = Column(Integer, nullable=False)
    total_frames = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=False) # 0-100
    
    ppe_violations = Column(Integer, nullable=False)
    zone_violations = Column(Integer, nullable=False)
    proximity_violations = Column(Integer, nullable=False)
    time_based_violations = Column(Integer, nullable=False)
    
    pipeline_status = Column(String, nullable=False) # 'PASS', 'FAIL'
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_metrics_status', 'pipeline_status'),
    )


# --- Document / Vector store models ---

# --- AUTH MODELS ---

class User(Base):
    """User accounts for RBAC."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'admin', 'viewer'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
    )

class RefreshToken(Base):
    """Rotating refresh tokens for session management."""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True) # FK handled by app logic or add ForeignKey constraint if desired
    token_hash = Column(String, nullable=False)
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True) # For rotation grouping
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True) # Audit field
    
    __table_args__ = (
        Index('idx_refresh_tokens_user', 'user_id'),
        Index('idx_refresh_tokens_family', 'family_id'),
    )


# --- Document / Vector store models ---

class Document(Base):
    """Track processed documents for RAG."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(String, nullable=False, unique=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    total_chunks = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_documents_status', 'status'),
        Index('idx_documents_created_at', 'created_at'),
    )


class DocumentVector(Base):
    """Vector store records for document chunks."""
    __tablename__ = "document_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), nullable=False, index=True) # Linked to Document
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False) # 384 dim for all-MiniLM-L6-v2
    metadata_ = Column("metadata", JSON, default=dict) # 'metadata' is reserved in SQLAlchemy Base
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_doc_vectors_embedding', 'embedding', postgresql_using='ivfflat'),
    )