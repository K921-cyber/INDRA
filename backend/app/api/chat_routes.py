"""
TRINETRA — Chatbot API Route
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.api_key_auth import require_api_key
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatTurn]] = None
    context: Optional[str] = None  # current scan/target data from the frontend, if any


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, _key: str = Depends(require_api_key)):
    history = [turn.model_dump() for turn in (req.history or [])]
    reply = await chat_service.get_reply(req.message, history, req.context)
    return ChatResponse(reply=reply)