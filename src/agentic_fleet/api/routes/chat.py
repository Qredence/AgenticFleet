"""
Routes for chat functionality.
"""

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from agentic_fleet.api.dependencies.services import get_chat_service
from agentic_fleet.schemas.message import Message as ChatMessage
from agentic_fleet.schemas.message import MessageCreate as ChatMessageCreate
from agentic_fleet.schemas.message import MessageUpdate as ChatMessageUpdate
from agentic_fleet.services.chat_service import ChatService

# Create router
router = APIRouter()


@router.get("/messages", response_model=dict[str, list[ChatMessage]])
async def list_messages(
    session_id: str, chat_service: ChatService = Depends(get_chat_service)
) -> dict[str, list[ChatMessage]]:
    """
    List all chat messages for a session.

    Args:
        session_id: The ID of the session to get messages for
    """
    try:
        messages = await chat_service.get_chat_history(session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages", response_model=ChatMessage)
async def create_message(
    message: ChatMessageCreate, chat_service: ChatService = Depends(get_chat_service)
) -> ChatMessage:
    """
    Create a new chat message.
    """
    try:
        return await chat_service.process_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}", response_model=ChatMessage)
async def get_message(
    message_id: str, chat_service: ChatService = Depends(get_chat_service)
) -> ChatMessage:
    """
    Get a specific chat message.
    """
    try:
        message = await chat_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/messages/{message_id}", response_model=ChatMessage)
async def update_message(
    message_id: str,
    message: ChatMessageUpdate,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatMessage:
    """
    Update a chat message.
    """
    try:
        updated_message = await chat_service.update_message(message_id, message)
        if not updated_message:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return updated_message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}", response_model=dict[str, bool])
async def delete_message(
    message_id: str, chat_service: ChatService = Depends(get_chat_service)
) -> dict[str, bool]:
    """
    Delete a chat message.
    """
    try:
        success = await chat_service.delete_message(message_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for real-time chat.
    """
    await websocket.accept()

    # Generate a session ID for this connection
    session_id = f"session_{uuid4().hex}"

    await chat_service.register_websocket(session_id, websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            # Parse the JSON data
            data = {}
            try:
                data = json.loads(data_text)
            except json.JSONDecodeError:
                # If not valid JSON, treat as plain text message
                data = {"content": data_text}

            await chat_service.process_websocket_message(session_id, data)
    except WebSocketDisconnect:
        await chat_service.unregister_websocket(session_id)
