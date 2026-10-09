# Learning Companion

A small local chat API for the LangChain and LangGraph classroom course. Open WebUI (already installed for you) sends your message here, a LangChain prompt and a Groq model write the answer, and the reply shows up in Open WebUI.

Open WebUI is supplied. You do not install, configure, or change it.

## Set up

1. Install dependencies: `uv sync`
2. Copy `.env.example` to `.env`.
3. In `.env`, set `GROQ_MODEL_NAME` to the model name your instructor gives you.
4. In `.env`, set `GROQ_API_KEY` to your own key. Put the key only in `.env`. It is never committed.

## Run

```
uv run python -m learning_companion
```

Run it from this folder. The app starts even if the key is still blank. If you chat before the key and model name are set, you get a clear message saying which one is missing. After editing `.env`, stop the app and start it again.

Quick checks (use `curl.exe` in PowerShell):

```
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s http://127.0.0.1:8000/v1/models
```

## Connect Open WebUI

Only the connection value on your side needs to match. In your existing Open WebUI connection, the base URL is:

```
http://127.0.0.1:8000/v1
```

Then pick the model named in your `GROQ_MODEL_NAME`. If your Open WebUI cannot reach `127.0.0.1` (for example, it runs in a container), ask your instructor for the right local address.

## What this seed does

Each chat message goes through one small flow: a fixed Learning Companion instruction plus your latest message, to Groq, back as text. It handles both normal and streaming replies on the same `/v1/chat/completions` route. Earlier messages in the chat are not used yet.

Not covered in this course: authentication, security hardening, databases, memory, RAG, or production deployment.
