"""Chat/agent routes."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from src.agents.agent_factory import AgentFactory
from src.core.exceptions import AgentError
from src.db.models import User
from src.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    tool_calls: Optional[list] = None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Chat with AI agent."""
    try:
        # Create agent
        agent = AgentFactory.create_agent()
        
        # Invoke agent
        result = agent.invoke({"input": request.message})
        
        return ChatResponse(
            answer=result.get("output", "No response generated"),
            tool_calls=result.get("intermediate_steps", [])
        )
        
    except AgentError as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check agent health."""
    try:
        # Try to create agent to verify configuration
        agent = AgentFactory.create_agent()
        return {"status": "healthy", "agent_available": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

