"""Pipeline state management."""

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class PipelineState(Enum):
    """Pipeline execution states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStateManager:
    """Manage pipeline execution state."""
    
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
    
    def create_state(self, job_id: Optional[str] = None) -> str:
        """Create new pipeline state."""
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        self.states[job_id] = {
            "job_id": job_id,
            "state": PipelineState.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "progress": 0.0,
            "metadata": {}
        }
        
        return job_id
    
    def update_state(
        self,
        job_id: str,
        state: Optional[PipelineState] = None,
        progress: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update pipeline state."""
        if job_id not in self.states:
            raise ValueError(f"Job {job_id} not found")
        
        if state:
            self.states[job_id]["state"] = state.value
        
        if progress is not None:
            self.states[job_id]["progress"] = progress
        
        if metadata:
            self.states[job_id]["metadata"].update(metadata)
        
        self.states[job_id]["updated_at"] = datetime.now().isoformat()
    
    def get_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline state."""
        return self.states.get(job_id)
    
    def delete_state(self, job_id: str):
        """Delete pipeline state."""
        if job_id in self.states:
            del self.states[job_id]

