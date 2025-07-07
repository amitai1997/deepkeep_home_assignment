"""Admin API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..models.schemas import UserStatus
from ..store.user_store import get_user_store

router = APIRouter(prefix="/admin", tags=["admin"])


@router.put("/unblock/{user_id}", response_model=UserStatus)
async def unblock_user(user_id: str) -> UserStatus:
    """
    Manually unblock a user and reset their violation count.

    Args:
        user_id: Unique identifier for the user to unblock

    Returns:
        Updated user status

    Raises:
        HTTPException: If user doesn't exist
    """
    user_store = get_user_store()

    # Check if user exists
    if user_id not in user_store._users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "code": "USER_NOT_FOUND",
                "details": f"User {user_id} does not exist in the system",
            },
        )

    # Unblock the user
    user_status = user_store.unblock_user(user_id)

    return user_status
