"""Endpoint conversationnel minimal (premier agent conversationnel).

Pour la Phase 1 : renvoie une réponse via le LLM par défaut. Il branchera
plus tard l'orchestrateur complet et la mémoire de conversation.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.router import Message, get_router

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    provider: str


_SYSTEM = (
    "Tu es FILON, un copilote d'achat francophone, sobre et honnête. Tu aides "
    "à décider quoi acheter, où, et à quel moment. Réponds brièvement."
)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    llm = get_router().for_task("default")
    reply = await llm.complete(
        [Message("system", _SYSTEM), Message("user", request.message)]
    )
    return ChatResponse(reply=reply, provider=llm.name)
