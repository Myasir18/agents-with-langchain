**Status:** Approved by instructor on 2026-10-09. Model provider changed from Grok (xAI) to Groq at the instructor's request on 2026-10-09.

# Architecture: Learning Companion Chatbot

A short, beginner LangChain and LangGraph classroom course. Participants build one small application, a **Learning Companion Chatbot**, step by step.

## The one classroom flow

```
Open WebUI
   → this local application's OpenAI-compatible chat endpoint
   → LangChain prompt and Groq model
   → answer in Open WebUI
```

Every story in the course extends this single flow. There is no second path.

## Open WebUI

Open WebUI is **already installed and working** for participants. It is the supplied chat client only. Participants must not reinstall, reconfigure, modify, or build it. The only thing a participant may adjust is the connection value on the application side (the local base URL, `http://127.0.0.1:8000/v1`, and the model they select).

## The capstone

The capstone is a small Learning Companion Chatbot. It is not a custom frontend and not a second demonstration application. The chat window is always Open WebUI.

## Application

A small FastAPI application in `src/learning_companion/`, with three routes:

| Route | Purpose |
|---|---|
| `GET /health` | Confirms the app is running. |
| `GET /v1/models` | Lists the configured Groq model so Open WebUI can select it. |
| `POST /v1/chat/completions` | The one chat route. Accepts the normal OpenAI-compatible chat request (`model`, text `messages` with `system`, `user` or `assistant` roles, `stream`). Returns normal JSON when `stream` is false and text-only streamed chunks, a stop chunk and `[DONE]` when it is true. |

### Chain behaviours

The app has two LangChain chains in `chain.py`. Both have the same shape, **prompt → Groq chat model → text output**, where the prompt is a fixed app instruction, then the recent earlier messages of the chat, then the user's latest message. Both use the same Groq model and `GROQ_*` settings and take the same inputs (`history`, `question`).

| Chain | Code | Responsibility |
|---|---|---|
| General chat | `prompt`, `build_chain` | The Learning Companion instruction, for greetings and ordinary conversation. Used for every message except `/study` ones. |
| Study helper | `study_prompt`, `build_study_chain` | Explains a beginner technical concept in plain language, with a small example where useful, and ends with one `Next step:` line. It does not claim to research, browse, or retrieve course data, or guarantee correctness. Used for messages that start with `/study`. |

During development the study helper can also be tried on its own with `uv run python -m learning_companion.try_study "<question>"`, which prints one answer and is not part of the app's routes.

### Route selection

One visible Python rule in `main.py` (`choose_route`, then an `if`/`else` in the chat route) picks the chain:

- If the first word of the latest user message is exactly `/study` (lowercase, whole word; leading spaces are fine), the **study** route is used. Only that leading marker is removed from the current question. A bare `/study` with nothing after it gets a 400 error.
- Otherwise the **general** route is used and the question is unchanged.

Path: latest user message → `/study` check → study-helper chain or general-chat chain → the same normal JSON or streamed response. History follows the rules in the message flow below; earlier `/study` messages stay in history as they were sent.

Study answers start with the line `*Route: study helper*`, inside the normal answer text (no extra response fields). When Open WebUI sends that answer back as history, the app removes the label first so the model does not copy it. General answers get no label, so Open WebUI's background requests (chat titles, follow-ups) are not affected.

**Boundary:** this is deterministic application routing by a fixed text rule. It is not LLM classification, LangGraph, an agent, or multi-agent orchestration. The model never chooses the route.

## Message flow

1. Open WebUI sends the usual OpenAI-compatible request to `POST /v1/chat/completions`. It includes the earlier messages of the active chat.
2. The app takes the **latest `user` message** as the current question. If it has no plain text, the request gets a 400 error.
3. The messages before it become **history**: plain-text `user` messages become human messages and plain-text `assistant` messages become AI messages, in their original order. Only the last **10** are kept (`MAX_HISTORY_MESSAGES` in `chain.py`, about five turns). Client `system` messages, other roles, and non-text content (for example images or files) are skipped.
4. The `/study` check picks the study-helper or general-chat chain and removes the marker from the current question (see Route selection).
5. The chosen chain's LangChain prompt has three parts, in this order: the chain's fixed instruction as the **system message**, the history through a **messages placeholder**, then the current question as the **human message** through the `{question}` variable. No prompt text is built by joining strings.
6. The Groq model answers and the text output parser returns plain text.
7. The text goes back as normal JSON, or as streamed events when `stream` is true. Study answers start with the route label.

A `system` message sent by the client is **not** the app's instruction. It never goes into the system part and never replaces or edits the instruction. It is simply not used.

In development (`APP_ENV=development`) the app logs, per chat request: the method, path and body size in bytes; the request body (the payload Open WebUI sent, including the chat's messages) as pretty JSON; and the chosen route, then the prompt's message roles in order with their count, how many messages the client sent, and how many were not used (for example `chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0`). The payload log was added at the participant's request during Story 3.1. Only the body is logged, never headers, so it never logs keys or the app's instruction. Outside development nothing is logged.

## No persistence

The app stores nothing and keeps no memory. It has no database and no files for chats. History comes only from the current Open WebUI request and is dropped when the request is done. There is no memory across chats or app restarts: a new chat starts fresh, because Open WebUI only sends the messages of the active chat.

## Configuration

Settings live in `.env`, copied from the canonical `.env.example`:

| Setting | Value |
|---|---|
| `APP_ENV` | `development` |
| `GROQ_API_KEY` | blank in `.env.example`; the participant's real key goes only in their untracked `.env` |
| `GROQ_API_BASE_URL` | `https://api.groq.com` |
| `GROQ_MODEL_NAME` | blank in `.env.example`; supplied by the instructor |
| `HOST` | `127.0.0.1` |
| `PORT` | `8000` |

The app starts without a real key. It returns a readable configuration error only when a model call is attempted without one.

## Light boundaries

- API keys stay in an untracked `.env`. They are never committed, logged, or returned in a response.
- Application instructions stay separate from user messages. User text is passed into the prompt as a variable, never pasted into the instruction text.

## Out of scope for this course

Authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, and extensive tests.

## Stack

Python 3.12, UV, FastAPI, Pydantic settings, LangChain, the Groq LangChain integration (`langchain-groq`), Uvicorn, Ruff, pytest.

## Story map

- **Story 1.1:** this architecture and a minimal project seed. One Open WebUI message reaches Groq and the reply shows in Open WebUI. Only the latest user message is used.
- **Story 2.1:** a reusable two-part LangChain prompt (fixed app instruction plus the latest user message), a development-only prompt log, and the message-flow and no-persistence notes above. Still only the latest user message is used.
- **Story 2.2:** request-provided conversation history. The last 10 earlier `user` and `assistant` messages from the current request go between the app instruction and the latest question. Nothing is stored.
- **Story 3.1:** the study-helper chain, a second chain with its own instruction on the same model, history and prompt shape.
- **Story 3.2:** a visible `/study` rule in the chat route that picks the study-helper chain; every other message keeps using general chat. Study answers carry a route label; the dev log shows `route=general` or `route=study`.
- **Story 4.1:** the same `/study` choice becomes an explicit LangGraph route inside the app (not yet written).
