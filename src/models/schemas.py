"""Data transfer objects and schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    message: str = Field(..., description="User's chat message")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    response: str = Field(..., description="OpenAI response")
    user_id: str = Field(..., description="User identifier")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: str | None = Field(None, description="Additional error details")


class UserStatus(BaseModel):
    """User status data model."""
    
    user_id: str
    violation_count: int = 0
    is_blocked: bool = False
    blocked_until: datetime | None = None
    last_violation: datetime | None = None
    created_at: datetime
    updated_at: datetime