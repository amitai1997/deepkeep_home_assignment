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

    if not await user_store.user_exists(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "User not found",
                "code": "USER_NOT_FOUND",
                "details": f"User {user_id} does not exist in the system",
            },
        )

    user_status = await user_store.unblock_user(user_id)

    return UserStatus.model_validate(vars(user_status))
