# Story 2.2: Conversation History from Open WebUI

**Status:** Built. Waiting on the two-turn Open WebUI check (see Implementation record)
**Model provider:** Groq (`langchain-groq`), unchanged since Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

Story 2.1 gave the app a clean two-part prompt: the app's fixed Learning Companion instruction, then the latest user message. Every question is still answered on its own, so a follow-up like "show me another example" loses track of what "it" was.

This story lets the app use the earlier messages of the current chat. Open WebUI already sends them with every request. The app passes a short, recent slice of them to the model, in order, between its own instruction and the new question. It still saves nothing.

## What this story implements in plain English

- When you ask a follow-up in the same chat, Open WebUI sends the earlier questions and answers along with it. The app now hands the most recent ones to the model, so "now add one more item to it" is understood.
- Only the last 10 earlier messages are used (about five back-and-forth turns). Older ones are left out, so long chats stay small and fast.
- The app's own study-helper instruction always comes first and cannot be replaced. A "system" message from the chat window, or anything that is not plain text from you or the assistant, is quietly skipped.
- Nothing is remembered by the app. The history lives in Open WebUI's chat. A new chat starts fresh, and restarting the app forgets nothing because it never stored anything.

## Prerequisites

- Story 2.1 is built. Its changes to `chain.py`, `main.py` and `docs/architecture.md` are **uncommitted** in the working tree on branch `story-1-1-architecture-project-seed`. Build on them; do not revert or stash them.
- Story 2.1's Open WebUI checks were not yet run, and its record flags two open items: the participant's `.env` probably has a wrong `GROQ_API_BASE_URL` (it must be the host only, `https://api.groq.com`), and a test instance may still be listening on port 8010. Ask the participant to fix the base URL and confirm one normal Open WebUI reply works before starting. Stop any leftover instance.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`.
- **No new dependency and no new setting.** `MessagesPlaceholder`, `HumanMessage` and `AIMessage` come from `langchain-core`, which is already installed. Do not run `uv add`. Do not edit `.env.example`.
- Provider wording: the handout says "Grok". The project uses Groq since 2026-10-09. Keep the `GROQ_*` settings exactly as they are.
- Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1 and 2.1, `.env.example`, and the code: `chain.py`, the chat route and logging middleware in `main.py`, and `ChatMessage` in `schemas.py`.

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `src/learning_companion/chain.py` | History placeholder in the prompt, the message limit, the history conversion, and the updated dev helper |
| `src/learning_companion/main.py` | Split the request into history and the current question; pass history to the one chain; compact dev logging |
| `src/learning_companion/schemas.py` | Let `ChatMessage` accept unknown roles and non-text content so they can be skipped instead of rejected |
| `docs/architecture.md` | History flow, message limit, no-persistence boundary, story map |
| `docs/stories/story-2-2-conversation-history.md` | The Implementation record (see Handover) |

Leave alone: `settings.py`, `__main__.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/manual-tests.md` (it has its own update step), Stories 1.1 and 2.1, the handout files, and `tests/`.

### Steps

1. **Add the history slot to the prompt (`chain.py`).** Keep the name `prompt` and the `LEARNING_COMPANION_INSTRUCTION` wording. The prompt becomes three parts, in this order, each with a short comment:
   - the app's instruction as the `SystemMessage` (unchanged);
   - `MessagesPlaceholder("history")` from `langchain_core.prompts`, for earlier messages;
   - `HumanMessagePromptTemplate.from_template("{question}")` (unchanged).

   Always pass `history`, even as an empty list on a first question. Do not join message text into a string or use f-strings to build the prompt.

2. **Set a documented limit (`chain.py`).** Add a module constant `MAX_HISTORY_MESSAGES = 10` with a one-line comment. Only the most recent 10 earlier messages are kept; older ones are dropped. This is a code constant, not a new `.env` setting.

3. **Convert history to LangChain messages (`chain.py`).** Add a small helper (for example `to_history(messages)`) that takes the earlier client messages in their original order and returns LangChain messages:
   - role `user` with plain, non-empty text content becomes `HumanMessage`;
   - role `assistant` with plain, non-empty text content becomes `AIMessage`;
   - everything else is skipped: `system` messages, any other role (for example `tool`), and content that is not a plain string (for example a list of image or file parts, or no content);
   - then keep only the last `MAX_HISTORY_MESSAGES`.

   History text goes into message objects, never into the instruction. Because the placeholder inserts messages as they are, braces like `{x}` in old messages are kept as plain text.

4. **Accept, then skip, unsupported messages (`schemas.py`).** Today `ChatMessage` only allows `system`, `user`, `assistant` with string content, so an unusual message makes the whole request fail with 422. Change it to `role: str` and `content: str | list | None = None`. The request shape is the same OpenAI-compatible shape; it just no longer rejects messages the app is going to skip. Response helpers stay unchanged.

5. **Split the request (`main.py`).** Replace `latest_user_message` with a small function that finds the **last `user` message** and returns:
   - the question: that message's text. If there is no `user` message, keep the existing 400 "The request has no user message." If its content is not plain, non-empty text, return a 400 with the same error type and a short message such as "The latest user message has no plain text.";
   - the earlier messages: everything before it, passed through `to_history`;
   - an ignored count for the log: client messages that did not go into the prompt (skipped, over the limit, or after the question).

   A client `system` message is never placed in the system part and never replaces or edits the app's instruction. In this story it is simply not used.

   Build `inputs = {"history": ..., "question": ...}` once, and give that same `inputs` to the one chain from `build_chain` on both the normal path (`ainvoke`) and the streaming path (`astream`). `build_chain` stays prompt → `ChatGroq` → `StrOutputParser`. No second chain, prompt, or route. Response JSON and SSE shapes do not change.

6. **Keep dev logging compact.**
   - `describe_prompt(inputs)` keeps returning one line of roles in order and the count, never message text. With history it reads, for example, `roles=system,human,ai,human count=4`.
   - The per-request line in `main.py` adds the ignored count, for example `chat prompt: roles=system,human,ai,human count=4 client_messages=3 ignored=0`. It is still logged only when `APP_ENV` is `development`, through the existing `uvicorn.error` logger, after the request checks and before the normal/streaming branch.
   - The existing `log_request_payload` middleware prints every request body as pretty JSON. With history that becomes a large message body on every turn, which this story must not log. Change it to one short line with the method, path and body size, for example `POST /v1/chat/completions body=2140 bytes`. Never log keys, the instruction text, or message bodies.

7. **Update `docs/architecture.md`.** Edit in place, keep it short, keep the `Status:` line as it is.
   - **Message flow:** the app finds the latest `user` message as the question; earlier plain-text `user` and `assistant` messages become history, in order, capped at `MAX_HISTORY_MESSAGES` (10); the prompt is system instruction → history → current question; client `system` messages and unsupported roles or content are skipped. Remove the "Earlier messages are not used yet" wording.
   - **Development log:** replace the sentence about printing full payloads with the compact lines from step 6.
   - **No persistence:** history comes only from the current Open WebUI request. The app has no database, files or memory for chats, saves nothing after the request, and has no memory across chats or restarts.
   - **Story map:** Story 2.2 is request-provided conversation history (last 10 earlier messages, no persistence). Add Story 3.1 as the next step, not yet written.

8. **Stay in scope.** Do not add a database, persistent or cross-session memory, chat IDs, summarising of old messages, token counting, RAG, tools, MCP, routing, LangGraph, a new endpoint, a new setting or dependency, a new UI, an Open WebUI plugin, an evaluation harness, or a test suite.

## Completion checks

Run only these, in this order. Run the app in a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do steps 3 and 4 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. `uv run python -m learning_companion` starts without errors on port 8000.
3. **First question.** In Open WebUI, start a **new chat** with the configured model and ask:
   > What is a Python list? Give one short example with three fruits.

   Expect a short answer with a small list such as `fruits = ["apple", "banana", "cherry"]`. The terminal line for it shows `roles=system,human count=2 client_messages=1 ignored=0`.
4. **Follow-up that depends on it.** In the same chat ask:
   > Now show me how to add one more fruit to it.

   Expect an answer that uses the same list from the first answer (for example `fruits.append("orange")`) without asking what "it" means. The terminal line shows `roles=system,human,ai,human count=4 client_messages=3 ignored=0`.

   Open WebUI may also send background requests (for example to name the chat or suggest follow-ups). They make their own lines, often with a different role pattern; that is expected. If the participant has a system prompt set in Open WebUI, `client_messages` is one higher and `ignored=1`, and the roles still start with a single `system`.
5. Check the terminal output from steps 3 and 4: no key, no instruction text, no question or answer text, and no full request bodies.
6. Read `main.py`: the three routes and response shapes are unchanged, and both the normal and the streaming path use the same `inputs` with the one chain from `build_chain`. Then run `git status --short` and confirm only the files in the table above changed (plus the Story 2.1 changes and untracked handout files already present).
7. Stop the app.

**Expected two-turn Open WebUI result:** the first reply explains a Python list with a three-fruit example; the second reply adds a fourth fruit to that same list, showing the app used the earlier turn. Both stream in as usual under the same model name, and the terminal shows `count=2` then `count=4` with roles `system,human` then `system,human,ai,human`.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- The two Open WebUI replies as the participant saw them (a short summary is fine) and the two dev log lines copied from the terminal (they hold no secrets). If steps 3 and 4 could not be done, say so plainly instead of reporting them as passed.
- Anything skipped or changed, and why.

Tell the instructor that `docs/architecture.md` was updated (history flow, 10-message limit, no-persistence boundary, story map) and point them to the Implementation record.

**What Story 3.1 will extend:** Story 3.1 is not written yet; it is the next step of this same chat flow. It takes over, unchanged unless it says otherwise: the three-part prompt (app instruction, history placeholder, current question), the history conversion and the `MAX_HISTORY_MESSAGES` limit, the rule that client `system` messages never replace the app's instruction, the compact dev log, and the no-persistence boundary (history comes only from the current request). The routes, JSON and SSE response shapes, `GROQ_*` settings, `.env.example`, Open WebUI connection and project layout stay as they are.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 5 (for the requests that were run), 6 and 7 pass. Check 2 passed on port 8020 instead of 8000 (see below). Checks 3 and 4 need the participant in Open WebUI and are **not yet run**.

### Files created or changed

As in the table above, with these notes:

- `chain.py`: the prompt is now `SystemMessage` (unchanged instruction), `MessagesPlaceholder("history")`, then `HumanMessagePromptTemplate.from_template("{question}")`. New `MAX_HISTORY_MESSAGES = 10` and `to_history(messages)`. `describe_prompt` and `build_chain` are unchanged apart from a docstring word.
- `main.py`: `latest_user_message` is replaced by `split_conversation(messages)`, which returns the history and the question and raises the 400 errors. One `inputs = {"history": ..., "question": ...}` feeds both `ainvoke` and `astream` on the one chain. The dev line adds `ignored=`. The payload middleware (renamed `log_request_size`) now logs only method, path and body size; the unused `json` import was removed.
- `schemas.py`: `ChatMessage` is now `role: str` and `content: str | list | None = None`. A request with only an unknown-role message now gets the readable 400 "no user message" instead of a 422.
- `docs/architecture.md`: message flow with history and the 10-message limit, compact dev logging, the no-persistence boundary, and the story map (2.2 filled in, 3.1 added as not yet written). `Status:` line unchanged.
- No new dependency, no new setting, nothing else touched.

### Commands actually run

| Command | Result |
|---|---|
| `uv run ruff format .` | pass (15 files left unchanged) |
| `uv run ruff check .` | pass, all checks passed |
| `uv run python <scratchpad>/check22.py` (offline, no model call; not in the check list) | pass: two-turn request gives `roles=system,human,ai,human count=4`; braces in old messages kept as text; client `system`, `tool`, list content and empty content skipped, and the app instruction stays the system message; 31 messages keep only the last 10 history messages (`q10` to `a14`); no user message and a non-text latest user message both give 400 |
| `Get-NetTCPConnection` on ports 8000 and 8010 | port 8000 in use by an instance the implementer did not start (left running); port 8010 free |
| `uv run python -m learning_companion` with `PORT=8020`, dummy `GROQ_API_KEY` and `GROQ_MODEL_NAME`, `APP_ENV=development` in the process environment (these override `.env`; the real key was not used) | pass: starts without errors |
| `curl.exe` on port 8020: `/health`; one `stream: true` chat POST with 4 client messages (system, user, assistant, user); one POST with only a `tool` message | `{"status":"ok"}`; the chat POST reached Groq and got HTTP 502 `provider_error` (401 Invalid API Key, expected with a dummy key; the key was not echoed); the tool-only POST got HTTP 400 "The request has no user message." |
| Stop the port 8020 instance; `git status --short` | pass: instance stopped; modified `architecture.md`, `chain.py`, `main.py`, `schemas.py`; untracked handout files and the 2.1 and 2.2 story files |

`pytest` was not run (no tests are written in this story).

### What the terminal showed (port 8020, dummy key)

```
INFO:     GET /health body=0 bytes
INFO:     POST /v1/chat/completions body=212 bytes
INFO:     chat prompt: roles=system,human,ai,human count=4 client_messages=4 ignored=1
INFO:     POST /v1/chat/completions body=56 bytes
```

The client `system` message was the one ignored message; the prompt still starts with the app's single `system` message. No key, instruction, or message text appears.

### Restart on port 8000 with the real settings

At the participant's request, the old port-8000 instance (pre-Story 2.2 code) was stopped and the app restarted with `uv run python -m learning_companion`, using the participant's `.env` (not read). Open WebUI was already running on port 8080 and was not touched.

| Command | Result |
|---|---|
| `curl.exe` `/health` and `/v1/models` on port 8000 | `{"status":"ok"}`; lists `openai/gpt-oss-120b` (`owned_by: groq`) |
| One `curl` `stream: false` chat POST with the two-turn conversation from checks 3 and 4 (the first answer written by hand) | HTTP 200. The reply used `fruits.append("orange")` on the same `["apple", "banana", "cherry"]` list. Groq accepted the call, so the base URL problem from Story 2.1 is no longer present |

Terminal line for that request:

```
INFO:     chat prompt: roles=system,human,ai,human count=4 client_messages=3 ignored=0
```

### Open WebUI result (checks 3 and 4)

Not yet run. The implementer cannot use Open WebUI. The app is running on port 8000 with this story's code. Still to do, by the participant or instructor: in a new chat, ask the two questions from checks 3 and 4 and report both replies and the two `chat prompt:` lines.

### Skipped or changed

- Check 2 first ran on port 8020 because port 8000 was taken; it later passed on port 8000 after the restart above.
- Checks 3 and 4 are not done. The role sequence was verified with `curl.exe` and the offline script instead, which does not show that the follow-up answer uses the earlier context.
