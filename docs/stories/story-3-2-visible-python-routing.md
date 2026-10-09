# Story 3.2: Visible Python Routing Between the Two Chains

**Status:** Built. Waiting on the Open WebUI checks (see Implementation record)
**Model provider:** Groq (`langchain-groq`), unchanged since Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

The app now has two LangChain chains in `chain.py`: the **general-chat chain** (`build_chain`) and the **study-helper chain** (`build_study_chain`). Open WebUI can only reach the general-chat chain. The study helper can be tried only with the development command `try_study`.

This story makes both chains reachable through the same Open WebUI chat endpoint, `POST /v1/chat/completions`. It adds one deliberately simple, visible Python rule in the chat route: if the latest user message starts with `/study`, use the study-helper chain; otherwise use the general-chat chain.

The rule is an ordinary `if`/`else` that participants can read in `main.py`. In Session 4, Story 4.1 replaces it internally with an explicit LangGraph route. The behaviour participants see stays the same.

## What this story implements in plain English

- An ordinary message such as "Hi! How are you today?" goes to the general-chat chain and gets the usual short, friendly reply, exactly as before.
- A message that starts with `/study`, such as `/study Explain what an API is`, goes to the study-helper chain. The app removes the `/study` marker first, so the helper sees only "Explain what an API is".
- The study reply starts with a small *Route: study helper* label, gives a plain explanation, and ends with one `Next step:` line. General replies get no label.
- Both kinds of message use the same Open WebUI chat, the same endpoint, and the same earlier messages as history. The choice is one fixed text rule in the code. The model does not choose.
- The app's terminal shows which route each request took (`route=general` or `route=study`).

## Prerequisites

- Story 3.1 is built on branch `story-3-1-study-helper-chain`. Its changes are **uncommitted**: `chain.py`, `main.py` (the payload log the participant asked for), `docs/architecture.md`, the new `try_study.py`, and the Story 3.1 file. Ask the participant whether to commit Story 3.1 first and start this story on a new branch, for example `story-3-2-visible-python-routing`. If they say no, build on the uncommitted work as it is. Do not revert or stash it.
- Story 3.1's Open WebUI check (its check 4) had not been run when its record was written. If it still has not been run, ask the participant to do it first. This story's checks use the same setup.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`. Do not add an Open WebUI plugin, function, or prompt shortcut.
- The participant's `.env` has a working `GROQ_API_KEY` and `GROQ_MODEL_NAME`, and `GROQ_API_BASE_URL` is the host only (`https://api.groq.com`).
- **No new dependency and no new setting.** Do not run `uv add`. Do not edit `.env.example`. LangGraph is **not** installed in this story.
- Provider wording: the handout says "Grok". The project has used Groq since 2026-10-09. Keep the `GROQ_*` settings exactly as they are.
- Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1 to 3.1, `.env.example`, and the code: both chains and `to_history` in `chain.py`; `chat_completions`, `split_conversation`, `event_stream` and the logging middleware in `main.py`; and `schemas.py`.

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `src/learning_companion/main.py` | The `/study` rule, the `if`/`else` that picks a chain, the study label on the answer text, the route in the dev log, and removal of the app's own label from history |
| `src/learning_companion/chain.py` | Only the `build_study_chain` docstring ("Not yet used by the chat route" is no longer true). No other line changes |
| `docs/architecture.md` | The `/study` rule, the selected-chain path, the boundary, the dev log line, and the story map |
| `docs/stories/story-3-2-visible-python-routing.md` | The Implementation record (see Handover) |

Leave alone: `schemas.py`, `settings.py`, `__main__.py`, `try_study.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/manual-tests.md` (it has its own update step), Stories 1.1 to 3.1, the handout files, and `tests/`.

### Steps

1. **Add the routing rule (`main.py`).** Add one small function, for example `choose_route(question) -> tuple[str, str]`, with a docstring saying it is the app's one visible routing rule and that Story 4.1 will replace it with a LangGraph route.
   - Split the question once on whitespace: `question.split(maxsplit=1)`.
   - If the first word is exactly `/study`, return `("study", <the rest>)`, where the rest is the text after the marker with spaces trimmed.
   - Otherwise return `("general", question)` with the question unchanged.

   Leading spaces before `/study` are fine. The match is lowercase only and must be a whole word, so `/studying` and `/Study` go to general chat. Remove only the leading marker; `/study` later in the text is left as it is. If nothing is left after the marker (the message is just `/study`), raise `ApiError(400, "Add a question after /study, for example: /study What is an API?", "invalid_request_error")`.

2. **Pick the chain with a plain `if`/`else` (`main.py`).** In `chat_completions`, after `split_conversation` and before building `inputs`:

   ```python
   route, question = choose_route(question)
   if route == "study":
       chain = build_study_chain(settings)
   else:
       chain = build_chain(settings)
   inputs = {"history": history, "question": question}
   ```

   Keep it this readable. Do not use a lookup table, a registry, or a class. The route is chosen by text only. Never ask the model which route to use.

3. **Keep history as in Story 2.2.** `split_conversation` and `to_history` keep their rules: the latest `user` message is the question; earlier plain-text `user` and `assistant` messages become history, in order, last 10 only; client `system` messages and non-text content are skipped. Only the **current** question loses its `/study` marker. Earlier user messages that started with `/study` stay in history as they are. Both chains get the same `inputs` shape, `{"history": ..., "question": ...}`.

4. **Show a route label on study answers (`main.py`).** Add a module constant, for example `STUDY_LABEL = "*Route: study helper*\n\n"`. Open WebUI shows it as one short italic line above the answer. It goes inside the normal answer text, so the response shape does not change:
   - normal path: `text = STUDY_LABEL + await chain.ainvoke(inputs)` for the study route;
   - streaming path: put the label in front of the first piece (`first = STUDY_LABEL + first`) before calling `event_stream`.

   General answers get **no** label. Open WebUI also sends background requests through this same endpoint (for example to name the chat or suggest follow-ups) and reads the replies as plain text or JSON. A label on general answers could end up in chat titles or break those replies. The `route=general` log line (step 6) shows the general route instead.

5. **Keep the label out of history (`main.py`).** Open WebUI sends earlier answers back on the next turn, labels included. A model that sees the label in its own earlier answers may copy it, so a general reply could look like a study reply. Before `split_conversation` passes earlier messages to `to_history`, remove `STUDY_LABEL` from the **start** of any `assistant` message with plain-text content (for example with `str.removeprefix` on a copy made with `model_copy`). Change nothing else. This is a small helper of a few lines in `main.py`, not a change to `to_history`.

6. **Add the route to the dev log (`main.py`).** Extend the existing development line with the route, before the roles:

   ```
   INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
   ```

   It is still one line per chat request, logged only when `APP_ENV` is `development`, after the request checks and before the normal/streaming branch. `describe_prompt(inputs)` can stay as it is, because both prompts have the same roles. The `ignored` count does not change. The line never holds message text, the instruction, or keys. Leave the request and payload middleware as they are.

7. **Use the existing response adapter.** Both routes go through the same code after the chain is chosen: `ainvoke` + `completion_body` for `stream: false`, and `astream` + `event_stream` for `stream: true`. Keep the first-piece check, `provider_error`, the 400 and 503 errors, the three routes, and the JSON and SSE shapes exactly as they are. Do not add response fields such as `route`, headers, or a new endpoint.

8. **Update one docstring (`chain.py`).** In `build_study_chain`, replace "Not yet used by the chat route; try it with learning_companion.try_study." with a line saying the chat route uses it for messages that start with `/study`. Change nothing else in `chain.py`.

9. **Update `docs/architecture.md`.** Edit in place, keep it short, keep the `Status:` line as it is.
   - **Chain behaviours:** general chat is used for every message except `/study` ones; the study helper is used for messages that start with `/study`. Remove "The only chain the chat route uses" and the Story 3.1 note that the chat route does not select the study helper yet. `try_study` stays as a development command.
   - **Route selection (new, short):** the rule from step 1; the selected-chain path (latest user message → `/study` check → study-helper chain or general-chat chain → same normal or streaming response); the marker is removed from the current question only; history follows the Story 2.2 rules; study answers start with the label, which is removed from history on the next turn. State the boundary plainly: **this is deterministic application routing by a fixed text rule. It is not LLM classification, LangGraph, an agent, or multi-agent orchestration.**
   - **Message flow:** add the `/study` check as a step between finding the question and building the prompt.
   - **Development log:** the `chat prompt:` line now starts with `route=general` or `route=study`.
   - **Story map:** Story 3.2 is the visible `/study` rule. Add Story 4.1 (not yet written): the same choice becomes an explicit LangGraph route.

10. **Stay in scope.** Do not add LLM-based routing or classification, more specialist chains or routes, review or retry steps, loops, tools, MCP, LangGraph, an agent, RAG, a database, persistent memory, a new endpoint, response field, setting or dependency, an Open WebUI plugin, broad tests, or production controls.

## Completion checks

Run only these, in this order. Run the app in a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do checks 3 and 4 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. `uv run python -m learning_companion` starts without errors on port 8000. If an older instance is already running there, stop it and restart, so the app runs this story's code.
3. **General route.** In Open WebUI, start a **new chat** with the configured model and send:
   > Hi! How are you today?

   Expected: the usual short, friendly Learning Companion greeting, streamed as before. It has no route label and no forced `Next step:` line.
4. **Study route, same chat.** In the **same** chat, send:
   > /study Explain what an API is

   Expected: the reply starts with the italic line *Route: study helper*, then gives a short, plain-language explanation of an API (possibly with one small example), and ends with **exactly one** line starting with `Next step:`. It does not repeat the word `/study` as if it were part of the question, and it does not claim to have searched or looked anything up.
5. **Inspect the route log.** In the app's terminal, find the lines for checks 3 and 4. Each request is a `POST /v1/chat/completions` line, which shows both replies came through the same endpoint. The `chat prompt:` lines should be:

   ```
   chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
   chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
   ```

   The second line shows the greeting turn was kept as history. Open WebUI's background requests (for example naming the chat) add their own `route=general` lines; that is expected. If the participant has a system prompt set in Open WebUI, `client_messages` is one higher and `ignored=1`. The `chat prompt:` lines hold no key and no instruction text. (The payload log added in Story 3.1 still prints the request body, including the messages. That is the existing development behaviour.)
6. `git status --short` shows only the files in the table above, plus the Story 3.1 work and handout files if they are still uncommitted.
7. Stop the app.

If Open WebUI is not available to the implementer, one `curl.exe` `stream: false` POST per route is a useful smoke check of the normal path. It does **not** replace checks 3 and 4.

**Expected Open WebUI result:** in one chat, the greeting gets the usual general-chat reply with no label. The `/study Explain what an API is` message gets a reply that starts with *Route: study helper*, explains an API plainly, and ends with one `Next step:` line. Both stream through `POST /v1/chat/completions`, and the terminal shows `route=general` then `route=study`.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- What the participant saw in Open WebUI for checks 3 and 4 (a short summary is fine, but copy the `Next step:` line and the label line exactly), and the two `chat prompt:` lines copied from the terminal (they hold no secrets). If checks 3 or 4 could not be done, say so plainly instead of reporting them as passed.
- Anything skipped or changed, and why.

Tell the instructor that `docs/architecture.md` was updated (the `/study` rule, the selected-chain path, the deterministic-routing boundary, the dev log line, the story map) and point them to the Implementation record.

**What Story 4.1 will extend:** Story 4.1 is not written yet. It is expected to start Session 4 by adding LangGraph and replacing the `choose_route` function and the `if`/`else` in `chat_completions` **internally** with an explicit LangGraph route: a small graph with a routing step that reads the same `/study` rule and sends the request to a general-chat step or a study-helper step, each using the existing chain. The routing stays a fixed text rule, not an LLM decision. It takes over, unchanged unless it says otherwise: the `/study` rule and marker removal, both chains and their instructions, `to_history` and the 10-message limit, the study label and its removal from history, the `route=` dev log line, the rule that client `system` messages never replace the app's instruction, the no-persistence boundary, the three routes, the JSON and SSE response shapes, the `GROQ_*` settings, `.env.example`, the Open WebUI connection, and the `try_study` command.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 2 and 6 pass. Checks 3 and 4 need the participant in Open WebUI and are **not yet run**, so check 5 has been done only for the `curl` requests below. Check 7 (stop the app) is not done: the app is left running on port 8000 so the participant can do checks 3 to 5.

Story 3.1 was not committed first. This story was built on top of its uncommitted work on branch `story-3-1-study-helper-chain`. Nothing was reverted, stashed or committed.

### Files created or changed

As in the table above, with these notes:

- `main.py`:
  - `STUDY_LABEL = "*Route: study helper*\n\n"`.
  - `choose_route(question)` holds the `/study` rule. The first word must be exactly `/study`. A bare `/study` gives a 400 error.
  - `without_study_label(message)` removes the label from the start of earlier assistant messages. `split_conversation` uses it before `to_history`.
  - In `chat_completions`, a plain `if route == "study": ... else: ...` picks `build_study_chain` or `build_chain`, and sets `label` (empty for general).
  - The label goes in front of the answer text: `label + await chain.ainvoke(inputs)` on the normal path, and `label + first` on the streaming path.
  - The dev line now starts `chat prompt: route=...`.
  - The import of `chain` functions became a multi-line import.
  - Middleware, errors, routes and response shapes are unchanged.
- `chain.py`: only the `build_study_chain` docstring changed.
- `docs/architecture.md`:
  - The chain behaviours table now says which messages use each chain.
  - New **Route selection** section: the rule, the path, the label and its removal from history, and the boundary (deterministic text rule, not LLM classification, LangGraph, an agent or multi-agent orchestration).
  - Message flow has a new step 4 for the `/study` check.
  - The dev log example shows `route=`.
  - Story map: 3.2 filled in, 4.1 added as not yet written.
  - `Status:` line unchanged.
- No new dependency or setting. Nothing in the "leave alone" list was touched.

### Commands actually run

| Command | Result |
|---|---|
| `uv run ruff format .` then `uv run ruff check .` (check 1) | pass: 20 files left unchanged, all checks passed |
| `uv run python <scratchpad>/check32.py` (offline, no model call; not in the check list) | pass. `/study Explain what an API is` → `study`, `Explain what an API is`. Leading and extra spaces are trimmed. `Hi! How are you today?`, `/studying hard`, `/Study x` and `why /study x` → `general`, unchanged. Bare `/study` → 400. An earlier labelled assistant answer reaches history without the label, and an earlier `/study` user message keeps its marker |
| `Get-NetTCPConnection` on port 8000, then `Stop-Process` | port 8000 was held by the Story 3.1 instance (`python -m learning_companion`, started 3:59 PM); stopped |
| `uv run python -m learning_companion` (check 2) | pass: starts without errors on port 8000 |
| `curl.exe` `/health` and `/v1/models` | `{"status":"ok"}`; model `openai/gpt-oss-120b` |
| `curl.exe` `stream: false` POST, "Hi! How are you today?" (not in the check list; does not replace check 3) | HTTP 200: "Hey there! I'm doing great, thanks for asking. 😊 How can I help you with your studies today?" No label, no `Next step:` |
| `curl.exe` `stream: false` POST, greeting turn as history + `/study Explain what an API is` (sent twice; the first time my output helper failed on a console encoding issue, not the app) | HTTP 200 both times; answer below |
| `curl.exe` `stream: true` POST, same study request | pass: first chunk is `{"role": "assistant", "content": "*Route: study helper*\n\n"}`, then text chunks, a `finish_reason: "stop"` chunk and `data: [DONE]` |
| `git status --short` (check 6) | pass: modified `architecture.md`, `chain.py`, `main.py`; untracked: this story, the Story 3.1 file, `try_study.py`, both handout files |

`pytest` was not run (no tests are written in this story). The curl calls used the participant's `.env`, which was not read or printed.

### Study answer (curl, normal path)

```
*Route: study helper*

An API (Application Programming Interface) is a set of rules that lets one piece of software talk to another, ... Think of it like a menu at a restaurant ... For example, a weather app calls a weather-service API to get the current temperature and displays it to you.

Next step: Try making a simple request to a public API (like the OpenWeatherMap API) using a tool such as Postman or curl.
```

Label line: yes. Plain explanation: yes. Exactly one `Next step:` line: yes. `/study` not treated as part of the question; no claim of searching.

### What the terminal showed (curl requests above)

```
INFO:     POST /v1/chat/completions body=110 bytes
INFO:     chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
INFO:     POST /v1/chat/completions body=251 bytes
INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
```

Both requests went through the same `POST /v1/chat/completions`. The payload log lines from Story 3.1 also printed each body; they are left out here.

### Open WebUI result (checks 3 and 4)

Not yet run. The implementer cannot use Open WebUI. The app is running on port 8000 with this story's code. Still to do, by the participant or instructor:

1. In a **new chat**, send "Hi! How are you today?".
2. In the **same** chat, send `/study Explain what an API is`.
3. Report both replies, the label line and the `Next step:` line, and the two `chat prompt:` lines (check 5).
4. Stop the app (check 7).

### Skipped or changed

- Story 3.1 was not committed and no new branch was made. The story asks the participant to decide that; nothing was committed without them.
- Checks 3 and 4 are not done. The curl calls show both routes, the label, the streaming shape and the route log, but they are not the Open WebUI checks.
- Check 7 is not done, on purpose, so checks 3 to 5 can be run against this code.
