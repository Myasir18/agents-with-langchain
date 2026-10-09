import json
import time
import uuid
from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """The part of the OpenAI chat-completions request this app uses.

    Extra fields sent by the client are ignored.
    """

    model: str
    messages: list[ChatMessage]
    stream: bool = False


def new_completion_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex}"


def completion_body(completion_id: str, model: str, text: str) -> dict:
    return {
        "id": completion_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


def chunk_event(
    completion_id: str,
    created: int,
    model: str,
    delta: dict,
    finish_reason: str | None = None,
) -> str:
    """One server-sent event carrying a chat.completion.chunk."""
    body = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(body)}\n\n"


def error_body(message: str, error_type: str) -> dict:
    return {"error": {"message": message, "type": error_type}}
