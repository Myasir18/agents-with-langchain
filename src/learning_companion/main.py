import time
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from learning_companion.chain import build_chain
from learning_companion.schemas import (
    ChatMessage,
    ChatRequest,
    chunk_event,
    completion_body,
    error_body,
    new_completion_id,
)
from learning_companion.settings import Settings, get_settings

app = FastAPI(title="Learning Companion")
STARTED_AT = int(time.time())


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, error_type: str):
        self.status_code = status_code
        self.message = message
        self.error_type = error_type


@app.exception_handler(ApiError)
async def handle_api_error(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.message, exc.error_type),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    name = get_settings().groq_model_name.strip()
    data = (
        [{"id": name, "object": "model", "created": STARTED_AT, "owned_by": "groq"}]
        if name
        else []
    )
    return {"object": "list", "data": data}


def latest_user_message(messages: list[ChatMessage]) -> str | None:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return None


def provider_error(exc: Exception, settings: Settings) -> ApiError:
    """Turn a Groq failure into a short error that never shows the key."""
    detail = str(exc)
    key = settings.groq_api_key.get_secret_value()
    if key:
        detail = detail.replace(key, "***")
    return ApiError(
        502,
        f"Groq did not accept the request ({type(exc).__name__}): {detail[:300]}",
        "provider_error",
    )


async def event_stream(
    model: str, first: str, rest: AsyncIterator[str]
) -> AsyncIterator[str]:
    completion_id = new_completion_id()
    created = int(time.time())
    yield chunk_event(
        completion_id, created, model, {"role": "assistant", "content": first}
    )
    async for piece in rest:
        yield chunk_event(completion_id, created, model, {"content": piece})
    yield chunk_event(completion_id, created, model, {}, "stop")
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    settings = get_settings()
    missing = settings.missing_setting()
    if missing == "GROQ_API_KEY":
        raise ApiError(
            503,
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key.",
            "configuration_error",
        )
    if missing == "GROQ_MODEL_NAME":
        raise ApiError(
            503,
            "GROQ_MODEL_NAME is not set. Ask your instructor for the model "
            "name and add it to .env.",
            "configuration_error",
        )

    question = latest_user_message(request.messages)
    if question is None:
        raise ApiError(400, "The request has no user message.", "invalid_request_error")

    chain = build_chain(settings)
    inputs = {"question": question}

    if not request.stream:
        try:
            text = await chain.ainvoke(inputs)
        except Exception as exc:
            raise provider_error(exc, settings) from exc
        return JSONResponse(completion_body(new_completion_id(), request.model, text))

    # Fetch the first piece before replying so a bad key or model name
    # becomes a normal error response, not a broken stream.
    pieces = chain.astream(inputs)
    try:
        first = await anext(pieces, "")
    except Exception as exc:
        raise provider_error(exc, settings) from exc
    return StreamingResponse(
        event_stream(request.model, first, pieces),
        media_type="text/event-stream",
    )
