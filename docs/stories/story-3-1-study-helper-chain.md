# Story 3.1: Study-Helper Chain

**Status:** Not started
**Model provider:** Groq (`langchain-groq`), unchanged since Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

Today the Learning Companion has one LangChain chain, the **general-chat chain**: app instruction → recent history → current question → Groq → text. It handles greetings and ordinary conversation, and Open WebUI uses it for every message.

This story adds a second, separately named chain: the **study-helper chain**. It explains a beginner technical concept in plain language and ends with one small suggested next learning step. It uses the same Groq model, the same request history and the same prompt shape. Only its instruction is different.

This story only builds the study helper and a small way to try it locally. Open WebUI keeps using the general-chat chain exactly as before. Choosing between the two chains is Story 3.2.

## What this story implements in plain English

- In Open WebUI, the chatbot behaves exactly as it does today: greetings, small talk and ordinary questions get the same short, friendly replies.
- During development, the implementer can run one local command, ask the study helper something like "What is an API?", and get a short plain-language explanation.
- The study helper adds a small example when it helps, and always ends with one small "Next step:" suggestion for what to learn next.
- The study helper is honest about what it is: it does not claim to search the web, look up course material, or guarantee its answer is correct.
- The study helper is not yet reachable from Open WebUI. Story 3.2 adds a simple, visible `/study` rule that picks it.

## Prerequisites

- Story 2.2 is built and committed (commit `7e66ef6`, branch `story-2-2-conversation-history`). Start this story on a new branch from there, for example `story-3-1-study-helper-chain`.
- Story 2.2's two-turn Open WebUI check (its checks 3 and 4) was not yet run when that record was written. If it still has not been run, ask the participant to do it first, because this story's Open WebUI check relies on the same working setup.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`.
- The participant's `.env` has a working `GROQ_API_KEY` and `GROQ_MODEL_NAME`, and `GROQ_API_BASE_URL` is the host only (`https://api.groq.com`). Story 2.2's record shows a real Groq call succeeding on port 8000.
- **No new dependency and no new setting.** Everything needed is already installed (`langchain-core`, `langchain-groq`). Do not run `uv add`. Do not edit `.env.example`.
- Provider wording: the handout says "Grok". The project uses Groq since 2026-10-09. Keep the `GROQ_*` settings exactly as they are.
- Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1, 2.1 and 2.2, `.env.example`, and the code: `chain.py`, the chat route and `split_conversation` in `main.py`, `settings.py`, and `schemas.py`.

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `src/learning_companion/chain.py` | **Add** the study-helper instruction, the study-helper prompt and `build_study_chain`. Existing code is not edited. |
| `src/learning_companion/try_study.py` | **New.** A small development-only command that runs the study-helper chain once and prints the answer. |
| `docs/architecture.md` | The two chain behaviours and their responsibilities; story map. |
| `docs/stories/story-3-1-study-helper-chain.md` | The Implementation record (see Handover). |

Leave alone: `main.py`, `schemas.py`, `settings.py`, `__main__.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/manual-tests.md` (it has its own update step), Stories 1.1 to 2.2, the handout files, and `tests/`.

### Steps

1. **Leave the general-chat chain untouched (`chain.py`).** Do not edit, rename, or reorder `LEARNING_COMPANION_INSTRUCTION`, `MAX_HISTORY_MESSAGES`, `prompt`, `to_history`, `describe_prompt` or `build_chain`. All new code is added **below** the existing code. In this document, `prompt` + `build_chain` is called the general-chat chain.

2. **Add the study-helper instruction (`chain.py`).** A module constant `STUDY_HELPER_INSTRUCTION`, fixed text with no variables, with a one-line comment like the existing one. A few sentences that ask for:
   - a short, plain-language explanation of the beginner technical concept the learner asks about;
   - one small example only when it helps (for example a few lines of code);
   - exactly one small suggested next learning step at the end, on its own line starting with `Next step:`;
   - saying plainly when it is not sure, instead of guessing.

   It must **not** say or imply that it searches, browses, retrieves course material, uses tools, or guarantees correctness. A suitable wording:

   > You are the Learning Companion's study helper. Explain the beginner technical concept the learner asks about in plain language, in a few short sentences. Add one small example only if it makes the idea clearer. End with exactly one small suggested next learning step, on its own line starting with "Next step:". If you are not sure about something, say so plainly.

3. **Add the study-helper prompt (`chain.py`).** A module-level `study_prompt`, built the same way as `prompt`, with a short comment on each part:
   - `SystemMessage(content=STUDY_HELPER_INSTRUCTION)`;
   - `MessagesPlaceholder("history")`;
   - `HumanMessagePromptTemplate.from_template("{question}")`.

   It takes the same inputs as the general-chat chain: `{"history": [...], "question": "..."}`, where history comes from the existing `to_history`. User text enters only through `history` and `{question}`. Do not join text into the instruction or use f-strings to build the prompt.

4. **Add `build_study_chain(settings)` (`chain.py`).** Returns `study_prompt | ChatGroq(...) | StrOutputParser()`. Create the `ChatGroq` model inside the function, per call, with the same three arguments as `build_chain` (`model`, `api_key`, `base_url` from the `GROQ_*` settings). This repeats a few lines from `build_chain` on purpose, so the general-chat chain stays untouched. Docstring: one line saying it is the study-helper chain and is not yet used by the chat route.

5. **Add a development-only command (`try_study.py`).** Run as:

   ```
   uv run python -m learning_companion.try_study "What is an API?"
   ```

   It:
   - takes the question from the command line (exit with a one-line usage message if none is given);
   - reads settings with `get_settings()` and, if `settings.missing_setting()` names a setting, prints a readable message naming it and exits with a non-zero code;
   - builds the chain with `build_study_chain(settings)` and calls `.invoke({"history": [], "question": question})` once (no streaming, no loop);
   - prints only the answer text;
   - on a Groq error, prints a short message with the error type only, never the key, and exits with a non-zero code.

   It is not imported by `main.py`, adds no route, and does not start the server. History is empty here; the chain itself accepts request history exactly like the general-chat chain.

6. **Update `docs/architecture.md`.** Edit in place, keep it short, keep the `Status:` line as it is.
   - In **Application**, replace the "one LangChain flow" paragraph with a short **Chain behaviours** list:
     - **General-chat chain** (`prompt`, `build_chain`): the Learning Companion instruction for greetings and ordinary conversation. It is the only chain the chat route uses.
     - **Study-helper chain** (`study_prompt`, `build_study_chain`): explains a beginner technical concept in plain language, with a small example where useful, and ends with one `Next step:` line. It does not claim to research, browse, or retrieve course data.
     - Both use the same shape (fixed instruction → request history → current question), the same Groq model and settings, and the same text output.
   - Say plainly: this story creates the study-helper capability only. The chat route does not select it yet; it can be tried only with `uv run python -m learning_companion.try_study "<question>"`. Selection between the chains is Story 3.2.
   - **Story map:** Story 3.1 is the study-helper chain (built, not yet selectable from Open WebUI). Story 3.2 adds the visible `/study` rule in the chat route (not yet written).

7. **Stay in scope.** Do not change the chat route, `split_conversation`, the response shapes, or the dev log. Do not add routing, a `/study` rule, LLM-based classification, more specialist chains, loops, review or retry steps, tools, MCP, LangGraph, an agent, RAG, a database, a new endpoint, a new setting or dependency, a new UI, an Open WebUI plugin, broad tests, or production controls.

## Completion checks

Run only these, in this order. Run the app in a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do check 4 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. `git diff --stat` shows no change to `main.py`, `schemas.py` or `settings.py`, and `git diff src/learning_companion/chain.py` shows **only added lines** (no `-` lines). This confirms the general-chat chain is untouched.
3. `uv run python -m learning_companion` starts without errors on port 8000. If an older instance is already running there, stop and restart it so it runs this story's code.
4. **General chat is unchanged.** In Open WebUI, start a **new chat** with the configured model and send:
   > Hi! How are you today?

   Expected: the usual short, friendly Learning Companion greeting, streamed as before under the same model name, with no forced `Next step:` line. The terminal line for it shows `chat prompt: roles=system,human count=2 client_messages=1 ignored=0`. Open WebUI may also send background requests (for example to name the chat); they make their own lines, which is expected.
5. **Study helper, one local call.** Run:

   ```
   uv run python -m learning_companion.try_study "What is an API?"
   ```

   Expected: a short, plain-language explanation of an API that a beginner can follow, possibly with one small example, ending with **exactly one** line starting with `Next step:` that suggests one small thing to learn or try. The answer does not claim to have searched, browsed, or looked anything up. Nothing else is printed: no key, no instruction text.
6. `git status --short` shows only the files in the table above (plus the untracked handout file already present).
7. Stop the app.

**Expected results:** Open WebUI gives the same general-chat reply as before this story, and the local command prints one plain study-helper explanation ending with one `Next step:` line.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- What the participant saw in Open WebUI for check 4, and the `chat prompt:` line copied from the terminal (it holds no secrets). If check 4 could not be done, say so plainly instead of reporting it as passed.
- The study-helper answer from check 5 (a short summary is fine, but copy the `Next step:` line exactly), and whether it had a plain explanation and exactly one next step.
- Anything skipped or changed, and why.

Tell the instructor that `docs/architecture.md` was updated (two chain behaviours, story map) and point them to the Implementation record.

**What Story 3.2 will extend:** Story 3.2 is not written yet. It is expected to add one visible, rule-based choice in the existing chat route in `main.py`: when the latest user message starts with `/study`, the request goes to the study-helper chain from `build_study_chain`; every other message keeps going to the general-chat chain from `build_chain`. This is a plain text rule, not an LLM classifier or an agent. Both paths will keep the same `inputs` (`history` and `question`), the same normal and streaming handling, and the same compact dev log. It takes over, unchanged unless it says otherwise: both chains and their instructions, `to_history` and the 10-message limit, the rule that client `system` messages never replace the app's instruction, the no-persistence boundary, the routes, JSON and SSE response shapes, `GROQ_*` settings, `.env.example`, the Open WebUI connection, and the `try_study` command.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 2, 3, 5 and 6 pass. Check 4 needs the participant in Open WebUI and is **not yet run**. Check 7 (stop the app) is not done: the app is left running on port 8000 so the participant can do check 4.

Work is on branch `story-3-1-study-helper-chain`, created from `story-2-2-conversation-history`. Nothing is committed yet.

### Files created or changed

As in the table above, with these notes:

- `chain.py`: added `STUDY_HELPER_INSTRUCTION` (the suggested wording from step 2), `study_prompt` (system instruction, `MessagesPlaceholder("history")`, `{question}`) and `build_study_chain(settings)`, all below the existing code. `git diff` shows 36 added lines and no removed lines, so the general-chat chain is untouched.
- `try_study.py` (new): two small additions beyond the story's description.
  - A Groq error is re-raised as `SystemExit` with only the error type. The plain `print` and `return 1` was flagged by Ruff (`BLE001`, blind `except`). It still prints one line and exits with code 1.
  - Before printing, it switches stdout to UTF-8. The first real run crashed with `UnicodeEncodeError`: the answer held a non-breaking hyphen (`\u2011`) that the Windows console code page (cp1252) cannot show. Windows participants would hit the same crash.
- `docs/architecture.md`: the "one LangChain flow" paragraph is replaced by a short **Chain behaviours** table (general chat vs study helper), with a note that only general chat is used by the chat route and that selection is Story 3.2. In the story map, 3.1 is filled in and 3.2 is added. `Status:` line unchanged.
- `main.py`, `schemas.py`, `settings.py` and everything in the "leave alone" list are unchanged. No new dependency or setting.

### Commands actually run

| Command | Result |
|---|---|
| `git switch -c story-3-1-study-helper-chain` | pass |
| `uv run ruff format .` | pass (18 files left unchanged) |
| `uv run ruff check .` (first run) | **fail**: `BLE001` in `try_study.py`; fixed as noted above |
| `uv run ruff format .` and `uv run ruff check .` (after the fix) | pass, all checks passed |
| `git diff --stat` and a count of removed lines in `git diff src/learning_companion/chain.py` (check 2) | pass: only `architecture.md` and `chain.py` modified; 0 removed lines in `chain.py` |
| `uv run python -m learning_companion.try_study "What is an API?"` (check 5, first run) | **fail**: the Groq call succeeded, but printing raised `UnicodeEncodeError` (cp1252); fixed as noted above |
| The same command (check 5, after the fix) | pass, exit 0 (answer below) |
| `uv run python -m learning_companion.try_study` with no question (not in the check list) | prints the usage line, exit 2 |
| `Get-NetTCPConnection` on ports 8000, 8010, 8020 | port 8000 held by the Story 2.2 instance (started 3:36 PM, pre-3.1 code); 8010 and 8020 free |
| `Stop-Process` on that instance, then `uv run python -m learning_companion` (check 3) | pass: starts without errors on port 8000 |
| `curl.exe -s http://127.0.0.1:8000/health` | `{"status":"ok"}` |
| `curl.exe` `/v1/models`, then one `stream: false` POST to `/v1/chat/completions` with "Hi! How are you today?" (not in the check list; does not replace check 4) | HTTP 200, model `openai/gpt-oss-120b`. Reply: "Hey there! I'm doing great, thanks for asking. How can I help you with your studies today?" A plain general-chat greeting with no `Next step:` line |
| `git status --short` (check 6) | pass: modified `docs/architecture.md`, `src/learning_companion/chain.py`; untracked `src/learning_companion/try_study.py`, this story file, and the handout file |

`pytest` was not run (no tests are written in this story). Both `try_study` calls and the curl call used the participant's `.env`, which was not read or printed.

### Study-helper answer (check 5)

Summary: an API is a set of rules that lets one piece of software talk to another, explained with a restaurant-menu comparison. One small example: a weather app asks a weather service's API for the current temperature. No claim of searching or looking anything up. It ends with exactly one next step:

```
Next step: Try making a simple request to a public API (e.g., the OpenWeatherMap API) using a tool like curl or Postman.
```

Plain explanation: yes. Exactly one `Next step:` line: yes.

### What the terminal showed (curl greeting above)

```
INFO:     POST /v1/chat/completions body=118 bytes
INFO:     chat prompt: roles=system,human count=2 client_messages=1 ignored=0
```

### Open WebUI result (check 4)

Not yet run. The implementer cannot use Open WebUI. The app is running on port 8000 with this story's code. Still to do, by the participant or instructor: in a **new chat**, send "Hi! How are you today?" and report the reply and the `chat prompt:` line. Then stop the app (check 7).

### Skipped or changed

- Check 4 is not done. The curl greeting shows the chat route still uses the general-chat chain, but it is not the Open WebUI check.
- Check 7 is not done, on purpose, so check 4 can be run against this code.

### Change requested during this story: payload log

After the checks above, the participant asked to see the request payload in the terminal when they chat in Open WebUI. This is outside the story's scope and reverses Story 2.2's choice to log only the body size.

- `main.py`: the middleware (renamed `log_request`) still logs `METHOD path body=N bytes`. In development it now also logs the request body as pretty JSON under `payload:`. Only the body is logged, never headers, so a key in an `Authorization` header cannot appear. Non-ASCII text is escaped (`\u00e9`) so the Windows console cannot crash on it. A body that is not valid JSON is logged as plain text. Outside `APP_ENV=development` nothing is logged. Routes, responses and the chat chain are unchanged.
- `docs/architecture.md`: the development-log paragraph now describes the payload log.
- Run: `uv run ruff format .` (1 file reformatted) and `uv run ruff check .` (pass). Restarted the app on port 8000. Two `curl.exe` POSTs with only a `system` message: the first sent bytes that were not valid UTF-8 (a Git Bash quirk) and was logged as plain text with a 400 parse error from FastAPI. The second was logged as pretty JSON and got the usual 400 "The request has no user message." No Groq call was made.
