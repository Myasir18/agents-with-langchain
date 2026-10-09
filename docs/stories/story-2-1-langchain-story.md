# Story 2.1: 

**Status:** Built. Waiting on the Open WebUI check (see Implementation record)
**Model provider:** Groq (`langchain-groq`), unchanged from Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

Story 1.1 sent one Open WebUI message to Groq with a small fixed prompt. This story turns that prompt into a clear, reusable building block with two separate parts: a fixed Learning Companion instruction that the app owns, and the current user message.

Behavior stays the same for the participant. The groundwork gets tidier so Story 2.2 can add conversation history on top of it.

## What this story implements in plain English

After this story, a participant using the chatbot:

- Sees the same chat in Open WebUI, the same model, and the same short, friendly study-helper answers.
- Gets answers shaped by the app's own fixed study-helper instruction. A `system` message sent by the chat window does not replace it.
- Still gets only the latest message answered. Earlier messages in the chat are not used yet (that is Story 2.2).
- Has nothing saved by the app. Each question is answered on its own, and restarting the app forgets everything.
- Can see one short line in the app's terminal during development, showing what kinds of messages were sent to the model, with no secrets and no hidden instruction text.

## Prerequisites

- Story 1.1 is built: the app starts, and `GET /health`, `GET /v1/models` and `POST /v1/chat/completions` work. Its Implementation record listed the Open WebUI checks (6 to 8) as not yet run. Finish them first, or at least confirm the participant has a working `.env` with a real key and model name, because this story's one check uses the same setup.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`.
- `uv` is installed and dependencies are already synced. **No new dependency.** The message and prompt classes come from `langchain-core`, which `langchain` already installs. Do not run `uv add`.
- Provider wording: the handout for this story says "Grok". The project moved to Groq on 2026-10-09 (see Story 1.1). Keep the existing `GROQ_*` settings and `.env.example` exactly as they are.
- Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Story 1.1, `.env.example`, and the existing code, especially `chain.py` and the chat route in `main.py` (with `schemas.py`).

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `src/learning_companion/chain.py` | The two-part prompt, and a small dev-only helper that describes it |
| `src/learning_companion/main.py` | Only to call that helper once per chat request. No route or response change |
| `docs/architecture.md` | Message flow, no-persistence boundary, story map |
| `docs/stories/story-2-1-langchain-prompt-template.md` | The Implementation record (see Handover) |

Leave alone: `schemas.py`, `settings.py`, `__main__.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/manual-tests.md` (it has its own update step), Story 1.1, the handout file, and `tests/`.

### Steps

1. **Rebuild the prompt as two separate parts (`chain.py`).** Keep the module-level name `prompt` and the existing `LEARNING_COMPANION_INSTRUCTION` wording.
   - Part one is the app's instruction, as a `SystemMessage` from `langchain_core.messages`. It is fixed and has no variables.
   - Part two is the current user message, as `HumanMessagePromptTemplate.from_template("{question}")` from `langchain_core.prompts`.
   - Combine them with `ChatPromptTemplate.from_messages([...])`, instruction first and user message second. Add a short comment naming each part.
   - Do not build the prompt by joining strings or with f-strings. User text enters only through `{question}`.

2. **Keep the one flow.** `build_chain(settings)` still returns prompt, then `ChatGroq`, then `StrOutputParser`. It still creates the model per chat request and passes `model`, `api_key` and `base_url` from the existing `GROQ_*` settings. The normal path (`ainvoke`) and the streaming path (`astream`) must both use that one chain. Do not add a second chain, a second prompt, or a second chat route.

3. **Use only the latest user message (`main.py`).** Keep `latest_user_message`. Only the latest `user` message goes into `{question}`.
   - A client `system` message is user-provided content. It never goes into the app's system part and never replaces or edits the instruction. In this story it is simply not used.
   - Earlier `user` and `assistant` messages are not used either. Do not add history handling. A request with no user message still gets the same 400 error.

4. **Add the dev-only inspection.**
   - In `chain.py`, add a small helper (for example `describe_prompt(inputs)`). It calls `prompt.format_messages(**inputs)` and returns one short line giving the message roles in order and the message count, for example `roles=system,human count=2`.
   - It must never include message text, settings, or the key. The hidden instruction and the user's question must not appear in it.
   - In `main.py`, log that line once per chat request, after the settings check and the user-message check and before the normal or streaming branch, so both paths log the same way. Include how many messages the client sent, for example `client_messages=3`.
   - Log only when `settings.app_env == "development"`. Use the existing `APP_ENV` setting and add no new one.
   - Python hides INFO log lines by default, so make sure the line really appears in the terminal running the app. The simplest way is `logging.getLogger("uvicorn.error")`, which already prints at INFO. If you use another logger, set it up so the line shows.

5. **Update `docs/architecture.md`.** Edit in place, keep it short, keep existing content that does not conflict, and leave the `Status:` line as it is.
   - Add a short **Message flow** section: the client's messages arrive; only the latest user message is picked; the prompt gets two parts in order (the app's instruction as the system message, then the user message as the human message); the Groq model answers; the text goes back as normal JSON or streamed events. Say that a client `system` message is not the app's instruction.
   - Add the **No persistence** boundary: the app stores nothing and keeps no memory. It has no database or files for chats. Each request is answered on its own, and the app never saves or replays earlier messages.
   - Fix the **Story map**: Story 2.1 is this prompt template (latest message only); Story 2.2 adds conversation history. This replaces the older line that gave history to Story 2.1. Do not edit Story 1.1's record.

6. **Stay in scope.** Do not add a command-line chatbot, a second chat path, conversation history, a database, persistent memory, RAG, tools, MCP, LangGraph, a new frontend, an Open WebUI plugin, a custom message format, a new setting or dependency, an evaluation harness, a test suite, or a security programme. The routes, JSON and SSE response shapes, and the Open WebUI connection stay exactly as they are.

## Completion checks

Run only these, in this order. Run the app in the background or a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do step 3 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. `uv run python -m learning_companion` starts without errors.
3. In the existing Open WebUI chat, with the existing connection and the configured model, start a new chat and ask one ordinary question, for example "What is a variable in programming?". Open WebUI streams by default, so this is a streaming request.
4. Look at the app terminal. For that question, the dev line shows the roles in order as `system` then `human`, a count of 2, and the number of messages the client sent. It shows no key, no instruction text and no question text. Open WebUI may send extra background requests (for example to name the chat); they produce their own lines, which is expected. If the chat already has earlier messages, the client count is higher but the prompt count stays 2.
5. Read `main.py`: the three routes and response shapes are unchanged, and both the normal and the streaming path call the one chain from `build_chain`. The normal path is not separately retested here. Then run `git status --short` and confirm only the files in the table above changed (plus the untracked handout file, which stays as it is).
6. Stop the app.

**Expected Open WebUI result:** one short, plain study-helper answer to the question, shown as usual under the same model name. The terminal shows the `system, human` line from check 4.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- What the participant saw in Open WebUI, and the dev log line copied from the terminal (it holds no secrets). If check 3 could not be done, say so plainly instead of reporting it as passed.
- Anything skipped or changed, and why.

Tell the instructor that `docs/architecture.md` was updated (message flow, no-persistence boundary, story map) and point them to the Implementation record.

**What Story 2.2 will extend:** conversation history. It will put the earlier `user` and `assistant` messages from the request between the app's instruction and the current message in this same prompt, using a LangChain messages placeholder. It will also decide how many earlier messages to keep and how a client `system` message is carried (as user-provided content, never in the system part). History still comes from each request and is never stored by the app. The routes, response shapes, settings, `.env.example` and project layout stay as they are.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 2 and 5 pass (check 2 on port 8010, see below). Checks 3 and 4 need the participant in Open WebUI and are **not yet run**. Check 6 (stop the app) is not finished: the implementer's test instance on port 8010 is still running.

### Files created or changed

As in the table above, with these differences:

- The story file now lives at `docs/stories/story-2-1-langchain-story.md` (renamed after it was written), so the record is here, not in `story-2-1-langchain-prompt-template.md`.
- `chain.py`: `prompt` is now a `SystemMessage` (the unchanged instruction) plus `HumanMessagePromptTemplate.from_template("{question}")`. New helper `describe_prompt(inputs)` returns `roles=system,human count=2` and never includes message text. `build_chain` is unchanged.
- `main.py`: imports `logging` and `describe_prompt`, and logs one line per chat request through `logging.getLogger("uvicorn.error")` when `APP_ENV` is `development`. It sits after the settings and user-message checks and before the stream/normal branch. No route or response change.
- `docs/architecture.md`: added **Message flow** and **No persistence** sections, and fixed the story map (2.1 is this prompt template, 2.2 is history). The `Status:` line is unchanged.
- No new dependency, no new setting, nothing else touched.

### Commands actually run

| Command | Result |
|---|---|
| `uv run ruff format .` | pass (13 files left unchanged) |
| `uv run ruff check .` | pass, all checks passed |
| Offline `uv run python -c ...` building the prompt with a question containing `{braces}` and a fake secret | not in the story's check list. Pass: roles in order `system`, `human`; braces kept as plain text; `describe_prompt` output held neither the question, the fake secret, nor the instruction |
| `uv run python -m learning_companion` (check 2, default port 8000) | **failed to bind**: port 8000 was already in use by an instance the implementer did not start |
| `curl.exe` `/health`, `/v1/models` and one `POST /v1/chat/completions` against that port-8000 instance | see "Needs attention" below |
| `uv run python -m learning_companion` with `PORT=8010` and dummy `GROQ_API_KEY` and `GROQ_MODEL_NAME` in the process environment (these override `.env`; the real key was not used) | pass: starts without errors |
| `curl.exe` on port 8010: `/health`, `/v1/models`, two `POST /v1/chat/completions` (`stream: true` and `stream: false`, each with 4 client messages: system, user, assistant, user), and one POST with only a `system` message | `/health` `{"status":"ok"}`; `/v1/models` lists the dummy model; both chat POSTs reached Groq and got HTTP 502 `provider_error` (401 Invalid API Key, expected with a dummy key, and the key was not echoed); the system-only POST got HTTP 400 "The request has no user message." as before |
| `git status --short` and `git diff --stat` | pass: only `chain.py`, `main.py` and `architecture.md` modified; untracked: the handout and this story file |

`pytest` was not run (no tests are written in this story).

### What the terminal showed

Both the streaming and the normal request on port 8010 printed this dev line, and the 400 request printed none:

```
INFO:     chat prompt: roles=system,human count=2 client_messages=4
```

Four client messages in, a two-message prompt out, instruction first. This was checked with `curl.exe` against a dummy key, not through Open WebUI.

### Open WebUI result (checks 3 and 4)

Not yet run. The implementer cannot use Open WebUI and has not read `.env`. Still to do, by the participant or instructor:

1. Stop the old instance on port 8000 and start it again with `uv run python -m learning_companion`. It was started before this story's edits, so it is still running the old code and will not print the dev line.
2. Fix the base URL first (see below).
3. In a new Open WebUI chat, ask one ordinary question and report the answer and the dev line from the app terminal.

### Needs attention

- **The instance on port 8000 appears to have a wrong `GROQ_API_BASE_URL`.** The implementer's first check ran against it by mistake: one `POST` (`stream: true`, a short test question) went to Groq with the participant's real settings and came back HTTP 502, with Groq reporting `Unknown request URL: POST /openai/v1/openai/v1/chat/completions`. The doubled `/openai/v1` means the participant's `.env` value likely ends in `/openai/v1`. `.env.example` says it must be the host only: `GROQ_API_BASE_URL=https://api.groq.com`. This was not read from `.env`; it is inferred from that error. It will break the Open WebUI check until fixed and the app is restarted. `.env.example` and the code were not changed for this.
- **The implementer's test instance on port 8010 is still running** (dummy key, local only). Stopping it was declined during the session, so it was left. Stop it with the command in the next line.

```
Get-NetTCPConnection -LocalPort 8010 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess }
```

### Skipped or changed

- Check 3 and check 4 as written (Open WebUI) are not done, as above. The dev line was verified through `curl.exe` instead, which does not replace the Open WebUI check.
- The normal (non-streaming) path was not retested through Open WebUI, as the story says. It was exercised once with `curl.exe` on port 8010 and logs the same line.
