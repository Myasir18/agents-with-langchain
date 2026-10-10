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

The app has four LangChain chains in `chain.py`, all on the same Groq model and `GROQ_*` settings. The two **answer chains** have the same shape, **prompt → Groq chat model → text output**, where the prompt is a fixed app instruction, then the recent earlier messages of the chat, then the user's latest message. They take the same inputs (`history`, `question`). The two **review chains** see only the draft answer (and the route or the reviewer's reason), never the history.

| Chain | Code | Responsibility |
|---|---|---|
| General chat | `prompt`, `build_chain` | The Learning Companion instruction, for greetings and ordinary conversation. Used for every message except `/study` ones. |
| Study helper | `study_prompt`, `build_study_chain` | Explains a beginner technical concept in plain language, with a small example where useful, and ends with one `Next step:` line. It does not claim to research, browse, or retrieve course data, or guarantee correctness. Used for messages that start with `/study`. |
| Reviewer | `review_prompt`, `build_review_chain` | Checks a draft against one fixed classroom rule (clear for a beginner, fits its route; JSON, titles and tags are approved as they are). Returns a structured `ReviewResult`: `decision` (`approve` or `improve`) and one short `reason`. |
| Improver | `improve_prompt`, `build_improve_chain` | Rewrites a draft once using the reviewer's reason: same meaning, same length or shorter, no new facts, keeps one `Next step:` line if there was one. Text output. |

During development the study helper can also be tried on its own with `uv run python -m learning_companion.try_study "<question>"`, which prints one answer and is not part of the app's routes.

### Routing and review workflow (LangGraph)

One small LangGraph workflow in `graph.py` picks the answer chain and then reviews the answer. The chat route in `main.py` runs it once per request (`build_graph`, then `run_graph`).

```
START → router ──general──→ general_chat ──┐
              └──study────→ study_helper ──┴→ answer_reviewer ──done──→ END
                                                 │        ▲
                            improve (count = 0)  ▼        │
                                           answer_improver (count → 1)
```

**State** (`ChatState`), kept for one request only:

| Field | Meaning | Written by |
|---|---|---|
| `user_message` | The current question (latest user message's text) | The app; the router removes a leading `/study` |
| `history` | Earlier messages, already converted by `to_history` | The app; no node changes it |
| `route` | `general` or `study` | `router` |
| `draft_answer` | The current answer: first the answer node's, then the improved one | `general_chat` or `study_helper`; then `answer_improver` |
| `review_decision` | The reviewer's latest verdict: `approve` or `improve` | `answer_reviewer` |
| `review_reason` | One short plain-English reason; the improver's note | `answer_reviewer` |
| `revision_count` | How many rewrites happened: 0 or 1 | The app sets 0; `answer_improver` adds 1 |
| `final_answer` | The accepted answer, before the study label | `answer_reviewer` |

**Nodes**, one job each:

- `router`: ordinary Python, no model call. If the first word of `user_message` is exactly `/study` (lowercase, whole word; leading spaces are fine), it writes `route=study` and removes only that leading marker. Otherwise it writes `route=general` and leaves the question unchanged. A bare `/study` with nothing after it raises `EmptyStudyQuestion`, which the chat route turns into a 400 error.
- `general_chat`: calls the general-chat chain and writes `draft_answer`.
- `study_helper`: calls the study-helper chain and writes `draft_answer`.
- `answer_reviewer`: calls the reviewer chain with the route and the draft, and writes `review_decision` and `review_reason`. When it accepts the draft, it also copies it to `final_answer`.
- `answer_improver`: calls the improver chain with the draft and the reviewer's reason, writes the new `draft_answer`, and adds 1 to `revision_count`. Nothing else.

**Edges:** `START → router`; a conditional edge from `router` that reads `route` and goes to `general_chat` or `study_helper`; each answer node → `answer_reviewer`; a conditional edge from `answer_reviewer` (`after_review`) that goes to `answer_improver` only when the decision is `improve` and `revision_count` is 0, and to `END` otherwise (approved, or `revision_count` is 1); `answer_improver → answer_reviewer`. No other edges.

**One-revision limit:** at most one rewrite and at most two reviews per question. The limit is `needs_improvement` in `graph.py` (`MAX_REVISIONS = 1`), used by both the reviewer and its edge. It is enforced by code, not by the model: on the second review the reviewer still gives its view, but the current draft is accepted whatever it says. LangGraph's recursion limit is not relied on.

**Terms:** a node is one focused piece of work, not automatically an agent. The router is ordinary application logic. The two answer nodes are small specialist behaviours that use the existing chains. The reviewer and improver are small LLM-powered specialist nodes (they may be called specialist agents in this classroom example). None of them plan, use tools, browse, retrieve information, or choose a route; the reviewer's decision only selects one of two fixed edges. A tool call (for example through MCP) could sit inside a future node, but MCP is not implemented.

The app adds the label: study answers start with the line `*Route: study helper*`, inside the normal answer text (no extra response fields). When Open WebUI sends that answer back as history, the app removes the label first so the model does not copy it. General answers get no label, so Open WebUI's background requests (chat titles, follow-ups) are not affected; the reviewer's rule approves their JSON and title replies as they are. Earlier `/study` messages stay in history as they were sent.

**Boundary:** the route is still a fixed text rule. It is not LLM classification, and the model never chooses the route. The graph is compiled without a checkpointer, so nothing is stored between requests.

**Deliberately out of scope:** any other loop, retry, or second rewrite; planners; LLM routing; more nodes or agents; tools, MCP, web search, RAG; human approval; persistence; observability platforms; and deployment.

## Message flow

1. Open WebUI sends the usual OpenAI-compatible request to `POST /v1/chat/completions`. It includes the earlier messages of the active chat.
2. The app takes the **latest `user` message** as the current question. If it has no plain text, the request gets a 400 error.
3. The messages before it become **history**: plain-text `user` messages become human messages and plain-text `assistant` messages become AI messages, in their original order. Only the last **10** are kept (`MAX_HISTORY_MESSAGES` in `chain.py`, about five turns). Client `system` messages, other roles, and non-text content (for example images or files) are skipped.
4. The graph runs: the router, one answer node, then the review path (see Routing and review workflow). The router picks the route and removes a leading `/study` from the current question.
5. The answer node's chain builds its LangChain prompt in three parts, in this order: the chain's fixed instruction as the **system message**, the history through a **messages placeholder**, then the current question as the **human message** through the `{question}` variable. No prompt text is built by joining strings.
6. The Groq model answers, the text output parser returns plain text, and the node writes it as `draft_answer`. The reviewer checks it and either accepts it as `final_answer` or sends it to the improver once, then checks the rewrite and accepts it.
7. The text goes back as normal JSON, or as streamed events when `stream` is true. Study answers start with the route label. The graph finishes before the reply starts, so a streamed answer arrives as one piece, not token by token. A reply takes two model calls (answer, review) or, when improved, four (answer, review, improve, review).

A `system` message sent by the client is **not** the app's instruction. It never goes into the system part and never replaces or edits the instruction. It is simply not used.

In development (`APP_ENV=development`) the app logs, per chat request: the method, path and body size in bytes; the request body (the payload Open WebUI sent, including the chat's messages) as pretty JSON; one line per review with the decision, the revision count, whether the draft was accepted, and the reviewer's short reason cut to 200 characters (for example `review: decision=improve revision_count=0 accepted=no reason=...`); a graph trace with the route, the last review decision, the revision count and the nodes that ran (for example `graph trace: route=study review=approve revision_count=1 nodes=router->study_helper->answer_reviewer->answer_improver->answer_reviewer`); and the chosen route, then the prompt's message roles in order with their count, how many messages the client sent, and how many were not used (for example `chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0`). The payload log was added at the participant's request during Story 3.1. Only the body is logged, never headers, so it never logs keys or the app's instructions; the review and trace lines hold no instruction text and no draft. Outside development nothing is logged.

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

Python 3.12, UV, FastAPI, Pydantic settings, LangChain, LangGraph, the Groq LangChain integration (`langchain-groq`), Uvicorn, Ruff, pytest.

## Story map

- **Story 1.1:** this architecture and a minimal project seed. One Open WebUI message reaches Groq and the reply shows in Open WebUI. Only the latest user message is used.
- **Story 2.1:** a reusable two-part LangChain prompt (fixed app instruction plus the latest user message), a development-only prompt log, and the message-flow and no-persistence notes above. Still only the latest user message is used.
- **Story 2.2:** request-provided conversation history. The last 10 earlier `user` and `assistant` messages from the current request go between the app instruction and the latest question. Nothing is stored.
- **Story 3.1:** the study-helper chain, a second chain with its own instruction on the same model, history and prompt shape.
- **Story 3.2:** a visible `/study` rule in the chat route that picks the study-helper chain; every other message keeps using general chat. Study answers carry a route label; the dev log shows `route=general` or `route=study`.
- **Story 4.1:** the same `/study` choice becomes a small LangGraph workflow in `graph.py`: a router node and two answer nodes using the existing chains, joined by explicit edges. The dev log adds a `graph trace:` line. Streamed answers arrive as one piece.
- **Story 4.2:** a bounded review path in the same graph: an answer-reviewer node and an answer-improver node, with at most one rewrite. The dev log adds `review:` lines and the review fields on the `graph trace:` line.

**Capstone outcome:** Open WebUI → `POST /v1/chat/completions` → one LangGraph workflow (a Python router picks general chat or the study helper; that chain writes a draft on Groq; a reviewer checks it; at most one improvement and one final review) → the answer in Open WebUI as normal JSON or streamed SSE. Nothing is stored, and there are no tools, MCP, retrieval, or web search.
