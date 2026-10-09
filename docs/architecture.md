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

Behind the chat route sits one LangChain flow: **prompt → Groq chat model → text output**. The prompt holds a fixed Learning Companion instruction plus the user's message. Normal and streaming requests use the same flow.

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
- **Story 2.1:** full prompt construction and conversation history.
