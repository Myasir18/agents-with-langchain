# Story 1.1: Architecture and Project Seed

**Status:** In progress: built, waiting on the Open WebUI checks (see Implementation record)
**Model provider:** Groq (`langchain-groq`). Changed from Grok (xAI) at the instructor's request on 2026-10-09.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

This is the first story in a short, beginner LangChain and LangGraph classroom course. It does two things in order: first it writes down and gets approval for the one flow the whole course is built on, then it creates a tiny working app that sends one Open WebUI message to Groq and shows the reply.

The end goal of the course is a small **Learning Companion Chatbot**. This story only plants the seed.

## What this story implements in plain English

After this story, a participant can:

- Start a small app on their own computer with one command.
- Open the chat window they already use (Open WebUI), pick the model their app offers, and get a real Groq reply that came through their own app.
- Keep their secret key in one private file that is never shared or saved to git.
- Start the app before the key is filled in, and see a clear, readable message (not a crash) if they try to chat too early.
- Read one short architecture page that explains how the pieces fit together.

## Prerequisites

- An instructor is available to approve Part A. Nothing in Part B starts without them.
- `uv` is installed (`uv --version`). Python 3.12 is available (uv can fetch it).
- Open WebUI is **already installed and working** for participants. It is the supplied chat window only. Do not reinstall, reconfigure, modify, or build it.
- The instructor has supplied the Groq model name. The participant has their own Groq API key.
- Repository state when this story was written: git repo on `main`, empty `docs/`, no other stories, and a root `.gitignore` already in place.
- Never read, print, paste, or commit the participant's `.env`. Never ask for the key in chat.

## Work to do

### Part A: Architecture (stop for approval)

Only `docs/architecture.md` may be created or changed in Part A. Do not create seed files, run `uv init`, install anything, or scaffold code.

1. Read `docs/config.yaml` (if present), `docs/architecture.md` (if present), the repository layout, and any stories in `docs/stories/`.
2. Create `docs/architecture.md`, or update it in place if it exists (keep existing content that does not conflict). Keep it short and plain. It must record:
   - **The one classroom flow:** Open WebUI → this local application's OpenAI-compatible chat endpoint → LangChain prompt and Groq model → answer in Open WebUI.
   - **Open WebUI** is already installed and working for participants. It is the supplied chat client only and is never reinstalled, reconfigured, modified, or built by participants.
   - **The capstone** is a small Learning Companion Chatbot. It is not a custom frontend and not a second demonstration application.
   - **The three routes:** `GET /health`, `GET /v1/models`, `POST /v1/chat/completions` (one chat route only, handling both normal and streaming replies).
   - **Configuration:** the six `.env` setting names from Part B, step 5; the instructor supplies the model name; the real key lives only in an untracked `.env`.
   - **Light boundaries:** API keys stay in an untracked `.env`; application instructions stay separate from user messages.
   - **Out of scope for the course:** authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, extensive tests.
   - **Stack:** Python 3.12, UV, FastAPI, Pydantic settings, LangChain, the Groq LangChain integration (`langchain-groq`), Uvicorn, Ruff, pytest.
   - **Story map:** Story 1.1 seeds the flow; Story 2.1 adds full prompt construction and conversation history.
   - A `Status:` line at the top, set to `Awaiting instructor approval`.
3. **Stop here.** Tell the instructor the path and ask exactly: *"Please review docs/architecture.md. Reply 'approved' to continue, or tell me what to change."*
4. Wait. Only an explicit approval counts. Silence, a thumbs-up on something else, or a partial answer does not. If changes are requested, edit `docs/architecture.md` only, then ask again.
5. On approval, set the `Status:` line to `Approved by instructor on <date>` and continue with Part B **in this same story**. If the session ends at the gate, resume this story at Part B; do not start a new one.

### Part B: Project seed (only after approval)

**Step 1: Create the project.** Run from the project path:

```
uv init --lib --name learning-companion --python 3.12
uv add fastapi pydantic-settings langchain langchain-groq uvicorn
uv add --dev ruff pytest
```

Review what `uv init` generated. Keep only what this story lists: empty out the sample code in `src/learning_companion/__init__.py`, and replace the generated `README.md` contents. A `.gitignore` already exists at the project root: keep it, and if `uv init` changed it, restore it (`git diff .gitignore`) and only add missing entries. Do not overwrite anything under `docs/`.

**Step 2: Files this story creates or changes.**

| File | Purpose |
|---|---|
| `docs/architecture.md` | Approved architecture (Part A) |
| `pyproject.toml`, `uv.lock`, `.python-version` | Python 3.12 and UV project; dependencies from Step 1; pytest pointed at `tests/` |
| `.env.example` | Canonical settings template (Step 5) |
| `.gitignore` | Already exists before this story starts. Confirm it ignores `.env`, `.venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`, build output; add only what is missing. It must **not** ignore `.env.example` or `uv.lock`. |
| `README.md` | Setup, run, and the Open WebUI connection value (Step 9) |
| `src/learning_companion/__init__.py` | Empty package marker |
| `src/learning_companion/__main__.py` | Starts Uvicorn using `HOST` and `PORT` from settings (`uv run python -m learning_companion`) |
| `src/learning_companion/settings.py` | Pydantic settings read from `.env` |
| `src/learning_companion/schemas.py` | Request and response shapes |
| `src/learning_companion/main.py` | FastAPI app and the three routes |
| `src/learning_companion/chain.py` | The LangChain prompt → Groq → text flow |
| `tests/.gitkeep` | Keeps the folder. No tests are written in this story. |

**Step 3: Settings (`settings.py`).** Pydantic settings that read `.env`, ignore unknown keys, and never fail at startup when values are blank. Treat a blank `GROQ_API_KEY` or blank `GROQ_MODEL_NAME` as "not configured". Read settings once at startup (editing `.env` means restarting the app).

**Step 4: Do not add anything outside the story.** No Claude or other-provider settings, no database or production settings, no tool calls, LangGraph, agents, MCP, advanced streaming, authentication, or a broad test suite.

**Step 5: `.env.example`.** Exactly these names and values, with a short comment saying the instructor supplies the model name and the participant puts their real key only in an untracked `.env`:

```
APP_ENV=development
GROQ_API_KEY=
GROQ_API_BASE_URL=https://api.groq.com
GROQ_MODEL_NAME=
HOST=127.0.0.1
PORT=8000
```

`GROQ_API_BASE_URL` is the Groq host only. Do not add `/openai/v1`: the Groq client adds that path itself, so a longer value would break every call. Add a one-line comment saying so.

**Step 6: Routes (`main.py`, `schemas.py`).**

- `GET /health` returns `{"status": "ok"}`.
- `GET /v1/models` returns `{"object": "list", "data": [...]}` with one entry for the configured Groq model: `{"id": "<GROQ_MODEL_NAME>", "object": "model", "created": <unix time>, "owned_by": "groq"}`. If the model name is blank, return an empty `data` list. This is not a model call, so it is not an error.
- `POST /v1/chat/completions` accepts `model` (string), `messages` (list of `{role, content}` where `role` is `system`, `user`, or `assistant` and `content` is plain text), and `stream` (boolean, default false). Ignore any extra fields Open WebUI sends. There is no second chat route.
  - **`stream: false`** returns one JSON object: `object: "chat.completion"`, an `id`, `created`, the request's `model`, and `choices: [{"index": 0, "message": {"role": "assistant", "content": "<reply>"}, "finish_reason": "stop"}]`. `usage` may be omitted.
  - **`stream: true`** returns `text/event-stream`. Each text piece is a line `data: {...}` followed by a blank line, with `object: "chat.completion.chunk"` and `choices: [{"index": 0, "delta": {"content": "<text>"}, "finish_reason": null}]` (the first chunk also carries `"role": "assistant"` in `delta`). After the last text piece send one stop chunk with `"delta": {}` and `"finish_reason": "stop"`, then `data: [DONE]`. Text only. No custom Open WebUI events.
  - The model used is always the configured `GROQ_MODEL_NAME`; the request's `model` is only echoed back.
  - If there is no `user` message, return a short readable error.

**Step 7: The one flow (`chain.py`).** A prompt → Groq chat model → text-output chain:

- The prompt has a fixed Learning Companion instruction (a few sentences: a friendly, plain-spoken study helper that gives short, clear answers and asks a follow-up when the question is vague) as the system message, and the **latest user message** as the human message. Pass the user's text in as a prompt variable. Never paste it into the instruction text, so instructions stay separate from user messages.
- Earlier messages and any `system` message sent by the client are ignored in this seed. That is Story 2.1.
- Use the Groq LangChain integration (`langchain-groq`, `ChatGroq`) and a plain text output parser. Pass the key, base URL, and model name explicitly from settings. Confirm the exact parameter names against the installed package rather than guessing.
- **Create the model object only when a chat request arrives**, not at import or startup. That is what lets the app start without a real key.
- Both normal and streaming requests use this same chain: one full call for `stream: false`, the chain's streaming output for `stream: true`.

**Step 8: Honest errors.** Before any model call, if `GROQ_API_KEY` or `GROQ_MODEL_NAME` is blank, return HTTP 503 with an OpenAI-style body: `{"error": {"message": "...", "type": "configuration_error"}}`. The message names the missing setting and says what to do (for example: "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."). Never include a key value. If Groq itself rejects the call (bad key, wrong model name), return HTTP 502 with the same body shape and a short message. For streaming requests, fetch the first chunk before returning the response so these errors arrive as normal errors, not as a broken stream.

**Step 9: `README.md`.** Short: what the app is; `uv sync`; copy `.env.example` to `.env`; instructor gives the model name; real key goes only in `.env`; run with `uv run python -m learning_companion`; and the **application-side Open WebUI connection value**: base URL `http://127.0.0.1:8000/v1` (the model to pick is the configured model name). State that Open WebUI is supplied and is not modified. If the participant's Open WebUI cannot reach `127.0.0.1` (for example, it runs in a container), ask the instructor for the right local address and record only that value. Do not change Open WebUI itself.

## Completion checks

Run only these lightweight checks, in this order. Run the app in the background or a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do those steps and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. `git check-ignore .env` prints `.env`; `git check-ignore .env.example` prints nothing.
3. With no `.env` present, `uv run python -m learning_companion` starts without errors.
4. `curl.exe -s http://127.0.0.1:8000/health` prints `{"status":"ok"}` (use `curl.exe` in PowerShell; plain `curl` is a different command there).
5. `curl.exe -s http://127.0.0.1:8000/v1/models` prints an empty `data` list. After the participant sets `GROQ_MODEL_NAME` in `.env` and the app is restarted, it lists that one model.
6. **Honest error:** with the model name set and `GROQ_API_KEY` still blank, the participant selects the model in Open WebUI (changing only the connection base URL if needed, per the README) and sends one message. Expected: a readable message naming `GROQ_API_KEY`, and the app keeps running.
7. **Streaming request:** participant puts the real key in `.env` (never in chat), restarts the app, and sends one message in Open WebUI. Open WebUI streams replies by default, so this is a streaming request. Expected: one Groq reply appears.
8. **Normal request:** in that chat's controls, turn off the stream option for this one chat (for example "Stream Chat Response" under Advanced Params), send one message, then turn it back on. This is a chat control, not a change to Open WebUI. Expected: one Groq reply appears all at once. If the control is not available, say so in the handover rather than reporting this check as passed.
9. Stop the app.

**Expected classroom result:** one Groq reply, in a short, plain, study-helper style, visible in Open WebUI, for both a streaming and a normal request.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed (the Step 2 list, noting anything different).
- The commands you actually ran, with pass or fail for each. List only what you ran.
- What the participant saw in Open WebUI for checks 6 to 8, and the connection base URL used if it differed from the default.
- Anything skipped or changed, and why.

Open WebUI may send extra background requests to the same chat endpoint (for example to name a chat). That is expected. Do not add special handling.

**What Story 2.1 will extend:** full prompt construction and conversation history. It will grow `chain.py` and the prompt so the whole conversation (not just the latest user message) is used, and decide how client `system` messages are treated. The routes, response shapes, settings, `.env.example`, and project layout from this story stay as they are.

When you finish, tell the instructor the story is complete and point them to the Implementation record.

---

## Implementation record

**Status:** Part A approved and Part B built (now on Groq). Completion checks 1 to 5 (no-`.env` half) pass. Checks 5 (model-listed half), 6, 7 and 8 need the participant in Open WebUI and are **not yet run**.

**Approval:** instructor approved `docs/architecture.md` on 2026-10-09.

### Files created or changed

As listed in Step 2, with these differences:

- `uv init --lib` also generated `src/learning_companion/py.typed`. It is not in the story, so it was removed.
- `pyproject.toml` has a project description and `[tool.pytest.ini_options] testpaths = ["tests"]`. The `authors` entry came from `uv init` (git config).
- `.gitignore` already existed and was left unchanged.
- `ChatXAI` parameter names confirmed from the installed package (`langchain-xai`): `model`, `api_key`, `base_url`.

### Provider change: Grok to Groq (2026-10-09)

After the first build, the instructor asked to use **Groq** instead of Grok. The spec above and `docs/architecture.md` now describe Groq. The tables below record what was run at each point, so they still show the original Grok commands.

- Dependency: `uv remove langchain-xai`, then `uv add langchain-groq` (`ChatGroq` takes `model`, `api_key`, `base_url`, confirmed from the installed package).
- Settings renamed: `GROK_API_KEY`, `GROK_API_BASE_URL`, `GROK_MODEL_NAME` are now `GROQ_API_KEY`, `GROQ_API_BASE_URL`, `GROQ_MODEL_NAME`. `.env.example` default base URL is `https://api.groq.com`, not an OpenAI-style `.../openai/v1` URL, because the Groq client appends `/openai/v1/...` itself.
- `/v1/models` now reports `owned_by: "groq"`. Error messages name the `GROQ_*` settings.
- Re-checked after the change (run with blank `GROQ_*` values in the process environment, so no real call could be made): `uv run ruff format .` and `uv run ruff check .` clean; app starts; `/health` returns `{"status":"ok"}`; `/v1/models` returns an empty `data` list; one extra POST to the chat route returned HTTP 503 `configuration_error` naming `GROQ_API_KEY`. An offline `build_chain` check with a dummy key built a `ChatGroq` pointing at `https://api.groq.com`. The app was stopped afterwards.
- **Existing `.env` files must be updated:** rename the three `GROK_*` lines to `GROQ_*` and use a Groq key and a Groq model name. Old `GROK_*` lines are ignored, so the app would report `GROQ_API_KEY is not set`.

### Commands actually run

| Command | Result |
|---|---|
| `uv init --lib --name learning-companion --python 3.12` | pass |
| `uv add fastapi pydantic-settings langchain langchain-xai uvicorn` | pass |
| `uv add --dev ruff pytest` | pass |
| `uv sync` | pass |
| `uv run ruff format .` | pass (reformatted 2 files) |
| `uv run ruff check .` | pass, all checks passed |
| `git check-ignore .env` / `git check-ignore .env.example` | pass: prints `.env`; prints nothing |
| `uv run python -m learning_companion` (no `.env` present) | pass: starts without errors |
| `curl.exe -s http://127.0.0.1:8000/health` | pass: `{"status":"ok"}` |
| `curl.exe -s http://127.0.0.1:8000/v1/models` | pass: `{"object":"list","data":[]}` |
| One extra `curl.exe` POST to `/v1/chat/completions` (`stream: true`, no key set) | not in the story's check list; run as a quick look at the config error. Result: HTTP 503, `configuration_error`, message names `GROK_API_KEY` |

The app was then stopped. `pytest` was not run (no tests are written in this story).

### Open WebUI results (checks 5 second half, 6, 7, 8)

Not yet run. The implementer cannot use Open WebUI and has not read `.env`. Still to do, by the participant or instructor:

1. Copy `.env.example` to `.env`; set `GROQ_MODEL_NAME`. Start the app with `uv run python -m learning_companion`. `/v1/models` should list that model.
2. Check 6: with `GROQ_API_KEY` still blank, select the model in Open WebUI (connection base URL `http://127.0.0.1:8000/v1`, or the instructor's local address) and send one message. Expect a readable `GROQ_API_KEY` message.
3. Check 7: add the real key to `.env` (not in chat), restart the app, send one message. Expect one streamed Groq reply.
4. Check 8: turn off the stream option for this one chat, send one message, turn it back on. Expect one Groq reply at once. Note here if the control is not available.

Not yet verified: the success paths (normal and streaming replies from Groq) and the 502 provider-error path. They have only been written, not exercised.

### What Story 2.1 will extend

Full prompt construction and conversation history. It will grow `chain.py` and the prompt so the whole conversation, not just the latest user message, is used, and decide how client `system` messages are treated. The routes, response shapes, settings, `.env.example`, and project layout stay as they are.
