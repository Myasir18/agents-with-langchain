# Story 4.1: LangGraph Routing Workflow

**Status:** Built. Waiting on the Open WebUI checks (see Implementation record)
**Model provider:** Groq (`langchain-groq`), unchanged since Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

Story 3.2 added one visible Python rule in `main.py`: `choose_route`, then an `if`/`else` in `chat_completions`. A message that starts with `/study` goes to the study-helper chain. Every other message goes to the general-chat chain.

This story swaps that `if`/`else` for one small **LangGraph workflow**, and changes nothing else in the app. The workflow has three steps, a router and two answer steps, joined by arrows you can read in code. The two existing LangChain chains are reused as they are. The FastAPI app, the one chat endpoint `POST /v1/chat/completions`, the Open WebUI connection, the `GROQ_*` settings, the history conversion, and the JSON and SSE response shapes all stay the same.

Participants see the same answers in Open WebUI as before. What is new is that the route, the shared state, the steps and the arrows are all visible in one file, and the terminal prints which steps each question went through.

## What this story implements in plain English

What happens to a question after it enters the chatbot:

- Open WebUI sends your message to the app, as it does today. The app takes your latest message and the earlier messages of this chat, using the same rules as before.
- A first step checks the first word of your message. If it is `/study`, the question goes to the study helper and `/study` is removed. Anything else goes to general chat. This is a fixed text rule. The model does not choose.
- The chosen helper asks the Groq model, with the same instruction and the same earlier messages as before, and writes down its answer.
- The app sends that answer back to Open WebUI in the same format as before. Study answers still start with *Route: study helper*.
- In development, the terminal prints one short line saying which route was taken and which steps ran, for example `route=study nodes=router->study_helper`.

### What the workflow keeps track of (the state)

While one question is being answered, the workflow keeps four pieces of information. Each step reads them and may fill some in. They exist only for that one request and are thrown away afterwards. Nothing is saved.

| Field | Plain English | Who fills it in |
|---|---|---|
| `user_message` | The current question: the text of your latest message. | The app, at the start. The router removes a leading `/study` from it. |
| `history` | The earlier messages of this chat, already converted by the existing `to_history` (last 10 plain-text user and assistant messages, study label removed). | The app, at the start. No step changes it. |
| `route` | Which helper should answer: `general` or `study`. | The router. |
| `final_answer` | The helper's answer text, before the app adds the study label. | The general-chat step or the study-helper step. |

### Words used in this story

- **Workflow** or **graph**: a small map of the steps a question goes through, written in code with LangGraph.
- **State**: the four shared fields above.
- **Node**: one focused piece of work in the workflow. A node is **not automatically an agent**. It is just a function that reads the state and writes some fields back.
- **Edge**: an arrow saying which node runs next. A **conditional edge** picks its next node by reading the state. `START` and `END` mark where the workflow begins and finishes.
- **Router**: ordinary application logic. It is the same fixed `/study` text rule as before, moved into a node. It is not an agent and it never calls the model.
- **General-chat and study-helper nodes**: each one calls an existing chain on the Groq model. You may call them small **specialist behaviours**. They do not plan, pick tools, or decide their own next step.
- **MCP**: a tool call (for example through MCP) could one day sit inside a node. MCP is **not** part of this story or this course step.

## Prerequisites

- Story 3.2 is committed (`797698a`, on branch `story-3-2-visible-python-routing`). Ask the participant whether to start this story on a new branch, for example `story-4-1-langgraph-routing-workflow`. Do not commit anything without them.
- Story 3.2's Open WebUI checks (3 and 4) had not been run when its record was written. If they still have not been run, ask the participant to run them first. This story uses the same checks.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`. No Open WebUI plugin, function, or custom response format.
- The participant's `.env` has a working `GROQ_API_KEY` and `GROQ_MODEL_NAME`, and `GROQ_API_BASE_URL` is the host only (`https://api.groq.com`). Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Provider wording: the handout says "Grok". The project has used Groq since 2026-10-09. Keep the `GROQ_*` settings exactly as they are.
- **One new dependency: `langgraph`**, added during implementation with `uv add langgraph`. No new setting. Do not edit `.env.example`.
- Read first: `docs/architecture.md`, Stories 1.1 to 3.2, `.env.example`, `chain.py` (both chains, `to_history`, `describe_prompt`), `main.py` (`chat_completions`, `split_conversation`, `without_study_label`, `choose_route`, `event_stream`, `provider_error`, the logging middleware), and `schemas.py`.

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `pyproject.toml`, `uv.lock` | `langgraph` added, by `uv add langgraph` only. No hand edits |
| `src/learning_companion/graph.py` (new) | The state, the three nodes, the edges, `build_graph`, and `run_graph` |
| `src/learning_companion/main.py` | Remove `choose_route` and the `if`/`else`; run the graph; map the bare-`/study` error to the same 400; add the dev trace line; send the final answer through the existing response adapter |
| `src/learning_companion/chain.py` | Only the `build_study_chain` docstring (it now says the study-helper node uses it). No other line changes |
| `docs/architecture.md` | The workflow section, message flow, dev log, stack, and story map (step 7) |
| `docs/stories/story-4-1-langgraph-routing-workflow.md` | The Implementation record (see Handover) |

Leave alone: `schemas.py`, `settings.py`, `__main__.py`, `try_study.py`, `.env.example`, `README.md`, `docs/manual-tests.md`, `docs/master-prompt-update-manual-tests.md`, Stories 1.1 to 3.2, the handout files, and `tests/`.

### Steps

1. **Add LangGraph.** Run `uv add langgraph`. Do not add any other package (no `langgraph-checkpoint-*`, no LangSmith, no tracing platform).

2. **Write the state (`graph.py`).** One `TypedDict`, for example `ChatState`, with exactly the four fields from the table above:

   ```python
   class ChatState(TypedDict):
       user_message: str
       history: list[BaseMessage]
       route: Literal["general", "study"]
       final_answer: str
   ```

   `history` is a plain list with no reducer (do not use `add_messages`). The app passes in only `user_message` and `history`. The nodes fill in `route` and `final_answer`.

3. **Write the three nodes (`graph.py`).** Each node takes the state and returns only the fields it changes. Give each a one-line docstring that says what kind of node it is.
   - **`router`** (ordinary Python, no model call): the `/study` rule from `choose_route`, moved here **unchanged**. Split `user_message` once (`split(maxsplit=1)`). If the first word is exactly `/study`, return `{"route": "study", "user_message": <the rest, trimmed>}`. Otherwise return `{"route": "general"}`. Lowercase whole word only, so `/studying` and `/Study` go to general. Only the leading marker is removed. If nothing follows `/study`, raise a small exception defined in `graph.py`, for example `EmptyStudyQuestion`, with the message `Add a question after /study, for example: /study What is an API?`. (`graph.py` must not import from `main.py`, so it cannot raise `ApiError` itself.)
   - **`general_chat`**: `await build_chain(settings).ainvoke({"history": state["history"], "question": state["user_message"]})`, then return `{"final_answer": answer}`.
   - **`study_helper`**: the same, with `build_study_chain(settings)`.

   The answer nodes do not add the study label, do not change history, and do not call anything else.

4. **Write the edges (`graph.py`).** One function, `build_graph(settings)`, builds and compiles the graph. The nodes are small functions inside it, so they can use `settings`. It is called once per chat request, like the chains today, so the app still starts without a key. The edges must be easy to read:

   ```python
   builder = StateGraph(ChatState)
   builder.add_node("router", router)
   builder.add_node("general_chat", general_chat)
   builder.add_node("study_helper", study_helper)
   builder.add_edge(START, "router")
   builder.add_conditional_edges(
       "router",
       next_node,  # returns state["route"]
       {"general": "general_chat", "study": "study_helper"},
   )
   builder.add_edge("general_chat", END)
   builder.add_edge("study_helper", END)
   return builder.compile()
   ```

   `compile()` gets **no checkpointer**, so nothing is stored between requests. No other nodes or edges: no reviewer, improver, loop, or retry.

5. **Run the graph and record the steps (`graph.py`).** Add `run_graph(graph, state) -> tuple[dict, list[str]]`. It runs the graph once with `graph.astream(state, stream_mode=["updates", "values"])`, collects the node names from the `updates` events in order, and keeps the last `values` event as the final state. It returns `(final_state, node_names)`. This is the real node sequence reported by LangGraph, not a guessed one.

6. **Use the graph in the chat route (`main.py`).**
   - Delete `choose_route` and the `if`/`else`. Keep the settings checks and `split_conversation` (with `without_study_label`) exactly as they are.
   - Run the graph inside one `try`:

     ```python
     try:
         state, nodes = await run_graph(
             build_graph(settings), {"user_message": question, "history": history}
         )
     except EmptyStudyQuestion as exc:
         raise ApiError(400, str(exc), "invalid_request_error") from exc
     except Exception as exc:
         raise provider_error(exc, settings) from exc
     ```

   - Add the label the same way as before: `label = STUDY_LABEL if state["route"] == "study" else ""`, then `text = label + state["final_answer"]`.
   - **Normal reply** (`stream: false`): `JSONResponse(completion_body(new_completion_id(), request.model, text))`, as today.
   - **Streaming reply** (`stream: true`): send `text` through the existing `event_stream`. Make its `rest` argument optional (`rest: AsyncIterator[str] | None = None`, loop only when given) and call `event_stream(request.model, text)`. The events stay exactly the same: a role chunk with content, a stop chunk, then `data: [DONE]`, with `text/event-stream`. The one visible difference is that the answer arrives as one piece after the graph finishes, instead of token by token. This is on purpose: the answer node writes a finished answer into the state, and Story 4.2's review needs the whole answer before anything is sent. Do not stream tokens from inside nodes in this story.
   - Because the model call now finishes before the response starts, the old "fetch the first piece" check is no longer needed. Errors are still normal JSON error responses on both paths.

7. **Add the dev trace (`main.py`).** In development only, after the graph finishes, log one compact line, then the existing `chat prompt:` line (now built from the final state: `{"history": state["history"], "question": state["user_message"]}`):

   ```
   INFO:     graph trace: route=study nodes=router->study_helper
   INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
   ```

   Neither line holds message text, the app instructions, or keys. Leave the request and payload middleware as they are. Do not add a trace field, header, or endpoint to the response.

8. **Update one docstring (`chain.py`).** In `build_study_chain`, say the study-helper node in `graph.py` uses it. Change nothing else.

9. **Update `docs/architecture.md`.** Edit in place, keep it short, keep the `Status:` line as it is.
   - Replace **Route selection** with a short **Routing workflow (LangGraph)** section:
     - the diagram:

       ```
       START → router ──route=general──→ general_chat → END
                     └──route=study────→ study_helper → END
       ```

     - the four state fields (the table above, shortened);
     - each node's one responsibility;
     - the edge rules: `START → router`; a conditional edge from `router` by `route`; each answer node → `END`;
     - the terminology: a node is not automatically an agent; the router is ordinary application logic; the answer nodes are small specialist behaviours using the existing chains; MCP could sit in a future node but is not implemented;
     - the boundary: the route is still a fixed text rule, never an LLM decision; no checkpointer, so nothing is stored;
     - still out of scope: review or improve steps, loops, retries, LLM routing, more agents or nodes, tools, MCP, web search, RAG, human approval, persistence, observability platforms, deployment.
   - **Message flow:** the `/study` check and the chain call become "the graph runs: router, then one answer node". Note that streamed answers now arrive as one piece.
   - **Development log:** add the `graph trace:` line.
   - **Stack:** add LangGraph.
   - **Story map:** fill in Story 4.1. Add Story 4.2 (not yet written): a bounded review path.

10. **Stay in scope.** No database, persistence, checkpointer, RAG, web search, tool execution, MCP, human approval, review step, loop, retry, extra node or agent, LLM routing, new endpoint, response field or setting, Open WebUI change, broad tests, security work, observability platform, or deployment.

## Completion checks

Run only these, in this order. Run the app in a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do checks 4 and 5 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. **Look at the graph shape** (no model call, no key printed):

   ```
   uv run python -c "from learning_companion.graph import build_graph; from learning_companion.settings import get_settings; print(build_graph(get_settings()).get_graph().draw_mermaid())"
   ```

   Expected: the nodes `router`, `general_chat` and `study_helper`; a solid edge `__start__ → router`; dotted (conditional) edges from `router` to `general_chat` and to `study_helper`; and solid edges from each answer node to `__end__`. Nothing else.
3. `uv run python -m learning_companion` starts without errors on port 8000. If an older instance is running there, stop it and restart.
4. **General path.** In Open WebUI, start a **new chat** with the configured model and send:
   > Hi! How are you today?

   Expected: the usual short, friendly greeting, with no route label and no forced `Next step:` line. It may appear all at once instead of word by word.
5. **Study path, same chat.** Send:
   > /study Explain what an API is

   Expected: the reply starts with *Route: study helper*, gives a short plain explanation of an API (maybe with one small example), and ends with **exactly one** `Next step:` line. It does not treat `/study` as part of the question or claim to have searched anything.
6. **Inspect the trace.** In the app's terminal, the lines for checks 4 and 5 should be:

   ```
   graph trace: route=general nodes=router->general_chat
   chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
   graph trace: route=study nodes=router->study_helper
   chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
   ```

   Each follows a `POST /v1/chat/completions` line, so both answers came through the same endpoint. Open WebUI's background requests (for example naming the chat) add their own `route=general` lines; that is expected. With a system prompt set in Open WebUI, `client_messages` is one higher and `ignored=1`.
7. `git status --short` shows only the files in the table above, plus any untracked handout files.
8. Stop the app.

If Open WebUI is not available to the implementer, one `curl.exe` `stream: false` POST per path, and one bare `/study` POST (expected: the same 400 message as Story 3.2), are useful smoke checks. They do **not** replace checks 4 and 5.

**Expected Open WebUI result:** in one chat, the greeting gets the usual general reply with no label. The `/study Explain what an API is` message gets a reply that starts with *Route: study helper*, explains an API plainly, and ends with one `Next step:` line. Both arrive through `POST /v1/chat/completions`, and the terminal shows `nodes=router->general_chat` then `nodes=router->study_helper`.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above, and the `langgraph` version `uv add` installed.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- The graph shape from check 2 (the mermaid text is fine).
- What the participant saw in Open WebUI for checks 4 and 5 (copy the label line and the `Next step:` line exactly), and the `graph trace:` and `chat prompt:` lines from the terminal (they hold no secrets). If checks 4 or 5 could not be done, say so plainly instead of reporting them as passed.
- Anything skipped or changed, and why.

Tell the instructor that `docs/architecture.md` was updated (graph diagram, state fields, node responsibilities, edge rules, terminology, what stays out of scope) and point them to the Implementation record.

**What Story 4.2 will extend:** Story 4.2 is not written yet. It is expected to add a **bounded review path** to this same graph: a review step after the answer nodes that checks the final answer and can send it for at most a fixed, small number of improvements before `END`. It will likely add a few state fields for that. It takes over, unchanged unless it says otherwise: `graph.py` with `ChatState`, the router and its `/study` rule, the two answer nodes and their chains, `run_graph` and the `graph trace:` line, the study label and its removal from history, `to_history` and the 10-message limit, no checkpointer and no persistence, the three routes, the JSON and SSE shapes (including sending the finished answer as one piece), the `GROQ_*` settings, `.env.example`, the Open WebUI connection, and the `try_study` command.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 2, 3 and 7 pass. Checks 4 and 5 need the participant in Open WebUI and are **not yet run**, so check 6 has been done only for the `curl` requests below. Check 8 (stop the app) is not done: the app is left running on port 8000 so the participant can do checks 4 to 6.

No new branch was made and nothing was committed. The work is uncommitted on `story-3-2-visible-python-routing` (Story 3.2 is committed as `797698a`). The participant can still move it with `git switch -c story-4-1-langgraph-routing-workflow`, since uncommitted changes go along. Whether Story 3.2's Open WebUI checks were ever run could not be confirmed.

### Files created or changed

As in the table above, with these notes:

- `pyproject.toml`, `uv.lock`: `uv add langgraph` added `langgraph>=1.2.14`. LangGraph **1.2.14** was already installed as a dependency of `langchain`, so no new package was downloaded. It is now a direct dependency. No hand edits.
- `graph.py` (new): `ChatState` with the four fields; `EmptyStudyQuestion`; `router` (the `choose_route` rule, unchanged); `next_node`; `build_graph(settings)`, where `general_chat` and `study_helper` are small async functions inside it; `run_graph`. The graph is compiled with no checkpointer.
- `main.py`:
  - Removed `choose_route` and the `if`/`else`. The chain imports became one import of `describe_prompt` and `to_history`, plus one import from `graph.py`.
  - `chat_completions` runs the graph in one `try`. `EmptyStudyQuestion` becomes the same 400 as before; anything else goes through `provider_error`.
  - In development, a new `graph trace:` line goes before the `chat prompt:` line, which is now built from the final state.
  - `event_stream`'s `rest` is now optional. The streaming path sends the labelled answer as one piece. The first-piece check was removed because the graph finishes before the reply starts.
  - Settings checks, `split_conversation`, `without_study_label`, `STUDY_LABEL`, the middleware, errors, routes and response shapes are unchanged.
- `chain.py`: only the `build_study_chain` docstring changed.
- `docs/architecture.md`: **Route selection** became **Routing workflow (LangGraph)**. It has the diagram, the state table, the node jobs, the edge rules, the terms, the boundary and what is out of scope. Message flow steps 4, 6 and 7, the dev log paragraph, the stack and the story map were updated (4.1 filled in, 4.2 added). The `Status:` line is unchanged.
- Nothing in the "leave alone" list was touched.

### Commands actually run

| Command | Result |
|---|---|
| `uv add langgraph` (step 1) | pass: `langgraph>=1.2.14` added to `pyproject.toml` and `uv.lock` |
| `uv run ruff format .` then `uv run ruff check .` (check 1) | pass: 1 file reformatted (a line in `main.py`), 22 unchanged; all checks passed |
| `uv run python -c "...draw_mermaid()"` (check 2) | pass: shape below |
| `uv run python <scratchpad>/check41.py` (offline, no model call; not in the check list) | pass. `/study Explain what an API is` → `study`, `Explain what an API is`. Leading and extra spaces are trimmed. `Hi! How are you today?`, `/studying hard`, `/Study x` and `why /study x` → `general`, question unchanged. Bare `/study` → `EmptyStudyQuestion` with the 3.2 message |
| `Get-NetTCPConnection` on port 8000, then `Stop-Process` | port 8000 was held by the Story 3.2 instance (`python -m learning_companion`, started 4:15 PM); stopped |
| `uv run python -m learning_companion` (check 3) | pass: starts without errors on port 8000 |
| `curl.exe` `/health` and `/v1/models` | `{"status":"ok"}`; model `openai/gpt-oss-120b` |
| `curl.exe` `stream: false` POST, "Hi! How are you today?" (does not replace check 4) | HTTP 200: "Hey there! I'm doing great, thanks for asking. How can I help you with your studies today?" No label, no `Next step:` |
| `curl.exe` `stream: false` POST, greeting turn as history + `/study Explain what an API is` (does not replace check 5) | HTTP 200; answer below |
| `curl.exe` `stream: true` POST, same study request | pass: 3 events. First chunk `role: assistant` with content starting `*Route: study helper*\n\nAn API`, then a `finish_reason: "stop"` chunk, then `data: [DONE]` |
| `curl.exe` POST with a bare `/study` | HTTP 400 `{"error":{"message":"Add a question after /study, for example: /study What is an API?","type":"invalid_request_error"}}` (same as Story 3.2) |
| `git status --short` (check 7) | pass: modified `architecture.md`, `pyproject.toml`, `chain.py`, `main.py`, `uv.lock`; untracked `graph.py`, this story, the 4.1 handout |

`pytest` was not run (this story writes no tests). The curl calls used the participant's `.env`, which was not read or printed.

### Graph shape (check 2)

```
__start__ --> router;
router -. &nbsp;general&nbsp; .-> general_chat;
router -. &nbsp;study&nbsp; .-> study_helper;
general_chat --> __end__;
study_helper --> __end__;
```

Nodes: `router`, `general_chat`, `study_helper`. One solid start edge, two dotted conditional edges, two solid end edges. Nothing else. (The mermaid header and style lines are left out.)

### Study answer (curl, normal path)

```
*Route: study helper*

An API (Application Programming Interface) is a set of rules that lets one piece of software talk to another. Think of it like a menu at a restaurant: ... For example, a weather app uses a public API to ask a server for the current temperature and then displays it to you.

Next step: Try sending a simple request to a public API (e.g., the OpenWeatherMap API) using a tool like curl or Postman.
```

Label line: yes. Plain explanation: yes. Exactly one `Next step:` line: yes. `/study` was not treated as part of the question, and there was no claim of searching.

### What the terminal showed (curl requests above)

```
INFO:     POST /v1/chat/completions body=111 bytes
INFO:     graph trace: route=general nodes=router->general_chat
INFO:     chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
INFO:     POST /v1/chat/completions body=298 bytes
INFO:     graph trace: route=study nodes=router->study_helper
INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
INFO:     POST /v1/chat/completions body=297 bytes
INFO:     graph trace: route=study nodes=router->study_helper
INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
INFO:     POST /v1/chat/completions body=79 bytes
```

These are the normal, streaming and bare-`/study` requests, in that order. The bare `/study` request logs no trace, because the router stops it before any answer node runs. The payload log lines from Story 3.1 also printed each body; they are left out here.

### Open WebUI result (checks 4 and 5)

Not yet run. The implementer cannot use Open WebUI. The app is running on port 8000 with this story's code. Still to do, by the participant or instructor:

1. In a **new chat**, send "Hi! How are you today?".
2. In the **same** chat, send `/study Explain what an API is`.
3. Report both replies, the label line and the `Next step:` line, and the `graph trace:` and `chat prompt:` lines (check 6).
4. Stop the app (check 8).

### Skipped or changed

- No new branch and no commit. The story asks the participant to decide that.
- Checks 4 and 5 are not done. The curl calls show both paths, the label, the streaming shape, the 400 and the trace, but they are not the Open WebUI checks.
- Check 8 is not done, on purpose, so checks 4 to 6 can be run against this code.
