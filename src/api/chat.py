"""Chat API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
import httpx

from ..models.schemas import ChatRequest, ChatResponse
from ..services.moderation import get_moderation_service
from ..services.openai_client import get_openai_client

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{user_id}", response_model=ChatResponse)
async def send_message(user_id: str, request: ChatRequest) -> ChatResponse:
    """
    Send a message to OpenAI via the chat gateway.

    Args:
        user_id: Unique identifier for the user
        request: Chat request containing the message

    Returns:
        Chat response from OpenAI

    Raises:
        HTTPException: If user is blocked or other errors occur
    """
    moderation_service = get_moderation_service()
    openai_client = get_openai_client()

    # Process message for violations and blocking
    has_violation, is_blocked = await moderation_service.process_message(
        request.message, user_id
    )

    # Block access only if the user was already blocked *before* this request.
    # When the current request itself triggers the final strike, we still allow
    # the response (has_violation is True and is_blocked is True).
    if is_blocked and not has_violation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "User is blocked",
                "code": "USER_BLOCKED",
                "details": "You have been temporarily blocked due to policy violations. Try again later or contact support.",
            },
        )

    # If violation detected but not blocked yet, still allow the message
    # (this follows the 3-strike policy - violations 1 and 2 don't block)

    try:
        # Forward message to OpenAI
        response_content = await openai_client.chat_completion(request.message)

        return ChatResponse(response=response_content, user_id=user_id)

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "OpenAI service unavailable",
                "code": "OPENAI_ERROR",
                "details": str(e),
            },
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "Invalid response from OpenAI",
                "code": "OPENAI_RESPONSE_ERROR",
                "details": str(e),
            },
        ) from e
