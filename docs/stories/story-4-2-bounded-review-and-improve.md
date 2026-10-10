# Story 4.2: Bounded Review and Improve

**Status:** Built. Waiting on the Open WebUI checks (see Implementation record)
**Model provider:** Groq (`langchain-groq`), unchanged since Story 1.1.
**Project path:** repository root (no `docs/config.yaml` existed when this story was written; if one exists when you start, use the project path it configures instead)

## Purpose

Story 4.1 turned the `/study` choice into a small LangGraph workflow in `graph.py`: a router, then one of two answer nodes, then `END`. Whatever the answer node writes goes straight back to Open WebUI.

This story adds a **bounded quality check** to that same graph. It adds two small Groq-powered nodes: an **answer reviewer** and an **answer improver**. The reviewer looks at the draft answer once. If the draft needs clearer wording, the improver rewrites it **once**, and the reviewer looks one last time. Then the workflow stops. There is at most one improvement per question, and the code enforces that limit.

Everything else stays as it is: the FastAPI app, the one chat endpoint `POST /v1/chat/completions`, the Open WebUI connection, the `GROQ_*` settings, the router and its `/study` rule, both answer chains, the history rules, the study label, and the normal JSON and streaming SSE response shapes.

This is the last story of the course. When it is done, the Learning Companion is the finished capstone (see Handover).

## What this story implements in plain English

What changes for a question after this story:

- The chosen helper (general chat or study helper) now writes a **draft**, not the final answer.
- A reviewer checks the draft **once** against one short, fixed classroom rule: is it clear for a beginner and right for its route? It says `approve` or `improve`, with one short reason.
- If it says `improve`, an improver rewrites the draft **once** using that reason, and the reviewer checks it one last time.
- After that one rewrite, the current draft is always accepted and sent to Open WebUI. There is no second rewrite, no retry, and no open-ended self-correction.
- In development, the terminal shows each review decision, the number of rewrites (0 or 1), and the steps the question went through.

### What the workflow keeps track of (the new state fields)

Story 4.1's state had four fields: `user_message`, `history`, `route` and `final_answer`. This story adds four fields and changes who writes `final_answer`. As before, they exist only for one request and are thrown away afterwards. Nothing is saved.

| Field | Plain English | Who fills it in |
|---|---|---|
| `draft_answer` | The answer as it currently stands: first the helper's answer, then the improved one if a rewrite happens. | `general_chat` or `study_helper`; then `answer_improver` if it runs |
| `review_decision` | The reviewer's latest verdict: `approve` (good enough) or `improve` (needs clearer wording). | `answer_reviewer` |
| `review_reason` | One short, plain-English sentence from the reviewer saying why. The improver uses it as its instruction for the rewrite. | `answer_reviewer` |
| `revision_count` | How many times the draft has been rewritten. Starts at 0 and can only reach 1. | The app sets 0 at the start; `answer_improver` adds 1 |
| `final_answer` | The answer that goes to Open WebUI (before the app adds the study label). This field already exists; it is now written by the reviewer when it accepts a draft, not by the answer nodes. | `answer_reviewer` |

### Words used in this story

- **Answer reviewer** and **answer improver**: small **LLM-powered specialist nodes**. Each makes one Groq call with its own fixed instruction and does one job. In this classroom example you may call them **specialist agents**. They do not use tools, browse, retrieve information, make plans, or choose routes.
- **Router**: still ordinary Python. It is the same fixed `/study` text rule as Story 4.1. It is not an agent and never calls the model.
- **Cycle**: the arrows reviewer → improver → reviewer form a small loop in the graph. It is **bounded**: Python code allows the improver to run only while `revision_count` is 0, so the loop can run at most once.
- **Structured decision**: the reviewer returns a small typed object (`decision` and `reason`), not free text, so the code can read the decision reliably.
- **MCP**: a tool call (for example through MCP) could one day sit inside a future node. MCP is **not** part of this story.

## Prerequisites

- Story 4.1 is built but was **uncommitted** when this story was written (its work sits on branch `story-3-2-visible-python-routing`, on top of commit `797698a`). Ask the participant whether to commit Story 4.1 first and start this story on a new branch, for example `story-4-2-bounded-review-and-improve`. Do not commit anything without them. If they say no, build on the uncommitted work as it is. Do not revert or stash it.
- Story 4.1's Open WebUI checks (4 to 6) had not been run when its record was written. If they still have not been run, ask the participant to run them first. This story uses the same setup.
- Open WebUI is already installed and working. Do not reinstall, reconfigure, modify, or build it. The connection base URL stays `http://127.0.0.1:8000/v1`. No Open WebUI plugin, function, custom event, or custom response format.
- The participant's `.env` has a working `GROQ_API_KEY` and `GROQ_MODEL_NAME`, and `GROQ_API_BASE_URL` is the host only (`https://api.groq.com`). Never read, print, paste, or commit `.env`. Never ask for the key in chat.
- Provider wording: the handout says "Grok". The project has used Groq since 2026-10-09. "Grok-powered" in the handout means the same Groq model and `GROQ_*` settings the app already uses. Keep those settings exactly as they are.
- **No new dependency and no new setting.** `langgraph`, `langchain-groq` and `pydantic` are already installed. Do not run `uv add`. Do not edit `.env.example`.
- Read first: `docs/architecture.md`, Stories 1.1 to 4.1, `.env.example`, `graph.py` (`ChatState`, `router`, `next_node`, `build_graph`, `run_graph`), `chain.py` (both chains, `to_history`, `describe_prompt`), `main.py` (`chat_completions`, `STUDY_LABEL`, `event_stream`, `provider_error`, the dev log lines), and `schemas.py` (`completion_body`, `chunk_event`).

## Work to do

### Files this story changes

| File | Change |
|---|---|
| `src/learning_companion/chain.py` | Add the reviewer's fixed rule, `ReviewResult`, `review_prompt`, `build_review_chain`; and the improver's instruction, `improve_prompt`, `build_improve_chain`. The two existing chains do not change |
| `src/learning_companion/graph.py` | Four new state fields; answer nodes write `draft_answer`; two new nodes; `needs_improvement` and `after_review`; the new edges; the review dev log line; module docstring |
| `src/learning_companion/main.py` | Start `revision_count` at 0; add the review decision and revision count to the `graph trace:` line. Nothing else |
| `docs/architecture.md` | The workflow section, chain table, message flow, dev log, story map, and capstone outcome |
| `docs/stories/story-4-2-bounded-review-and-improve.md` | The Implementation record (see Handover) |

Leave alone: `schemas.py`, `settings.py`, `__main__.py`, `try_study.py`, `.env.example`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/manual-tests.md`, `docs/master-prompt-update-manual-tests.md`, Stories 1.1 to 4.1, the handout files, and `tests/`.

### Steps

1. **Add the reviewer chain (`chain.py`).** Below the study-helper chain, add the reviewer's fixed classroom rule as a module constant, in the same style as the other instructions:

   ```python
   REVIEWER_INSTRUCTION = (
       "You review one draft answer from the Learning Companion, a chatbot for "
       "beginners. Classroom rule: approve the draft if a beginner can follow "
       "it and it fits its route. "
       "Route general: a short, friendly reply. "
       "Route study: a plain-language explanation of a beginner technical "
       "concept, with any technical term explained, ending with exactly one "
       'line that starts with "Next step:". '
       "Choose improve only if the draft clearly breaks this rule, for example "
       "unexplained jargon, one long dense paragraph, a missing or repeated "
       '"Next step:" line, or a claim to have searched or looked something up. '
       "If the draft is structured data such as JSON, or a short title or list "
       "of tags, approve it. "
       "Give one short plain-English reason."
   )
   ```

   The JSON/title sentence matters: Open WebUI sends background requests (chat titles, tags, follow-ups) through this same endpoint and expects those exact formats back. They take the general route and must pass review unchanged.

   Then add a small Pydantic model, a prompt, and a builder:

   ```python
   class ReviewResult(BaseModel):
       """The reviewer's structured decision."""

       decision: Literal["approve", "improve"]
       reason: str = Field(description="One short plain-English sentence.")


   review_prompt = ChatPromptTemplate.from_messages(
       [
           SystemMessage(content=REVIEWER_INSTRUCTION),
           HumanMessagePromptTemplate.from_template(
               "Route: {route}\n\nDraft answer:\n{draft}"
           ),
       ]
   )
   ```

   `build_review_chain(settings)` builds `ChatGroq` exactly like the existing builders and returns `review_prompt | model.with_structured_output(ReviewResult)`. The reviewer gets only the route and the draft. No history, no tools. The draft enters only through the `{draft}` variable, never pasted into the instruction.

2. **Add the improver chain (`chain.py`).** Add its fixed instruction:

   ```python
   IMPROVER_INSTRUCTION = (
       "You improve one draft answer from the Learning Companion, a chatbot for "
       "beginners, using one reviewer note. "
       "Rewrite the draft once so a beginner can follow it and the note is "
       "addressed. Keep the same meaning, and keep it the same length or shorter. "
       "Do not add new facts, links or sources, and do not claim to have "
       "searched or looked anything up. "
       'If the draft ends with a line starting with "Next step:", keep exactly '
       "one such line at the end. "
       "Return only the improved answer, with no comment about the review."
   )
   ```

   `improve_prompt` is the same shape as `review_prompt`, with the human template `"Reviewer note: {reason}\n\nDraft answer:\n{draft}"`. `build_improve_chain(settings)` returns `improve_prompt | model | StrOutputParser()`. Do not change the two existing chains or refactor how `ChatGroq` is built.

3. **Extend the state (`graph.py`).** Add exactly these fields to `ChatState`, each with a one-line comment like the existing ones:

   ```python
   draft_answer: str
   review_decision: Literal["approve", "improve"]
   review_reason: str
   revision_count: int
   final_answer: str  # already there; now written by the reviewer
   ```

   No reducers, no lists of past drafts, no other fields.

4. **Make the answer nodes write a draft (`graph.py`).** In `general_chat` and `study_helper`, change only the return value from `{"final_answer": answer}` to `{"draft_answer": answer}`. Nothing else in these nodes or in `router` changes.

5. **Write the one-revision rule (`graph.py`).** One small module function, used by both the reviewer and the edge, so the limit lives in one visible place:

   ```python
   MAX_REVISIONS = 1


   def needs_improvement(decision: str, revision_count: int) -> bool:
       """The one-revision limit: improve only a first draft the reviewer
       asked to improve. After one rewrite the draft is always accepted."""
       return decision == "improve" and revision_count < MAX_REVISIONS
   ```

6. **Add the reviewer node (`graph.py`, inside `build_graph`).** `answer_reviewer(state)`:
   - calls `build_review_chain(settings).ainvoke({"route": state["route"], "draft": state["draft_answer"]})`;
   - returns `{"review_decision": result.decision, "review_reason": result.reason}`;
   - when `needs_improvement(...)` is false, also returns `"final_answer": state["draft_answer"]`. That is both the "approved" case and the "limit reached" case. On the second review it still calls the model, so its honest view is logged, but whatever it says, the current draft becomes final;
   - in development only, logs one line (see step 9).

7. **Add the improver node (`graph.py`, inside `build_graph`).** `answer_improver(state)` calls `build_improve_chain(settings).ainvoke({"reason": state["review_reason"], "draft": state["draft_answer"]})` and returns `{"draft_answer": improved, "revision_count": state["revision_count"] + 1}`. It does nothing else: no tools, browsing, retrieval, planning, history, or routing.

8. **Wire the bounded edges (`graph.py`).** Keep `START → router` and the router's conditional edge exactly as they are. Replace the two `→ END` edges from the answer nodes with:

   ```python
   builder.add_node("answer_reviewer", answer_reviewer)
   builder.add_node("answer_improver", answer_improver)
   builder.add_edge("general_chat", "answer_reviewer")
   builder.add_edge("study_helper", "answer_reviewer")
   builder.add_conditional_edges(
       "answer_reviewer",
       after_review,  # "improve" only when needs_improvement(...) is true
       {"improve": "answer_improver", "done": END},
   )
   builder.add_edge("answer_improver", "answer_reviewer")
   return builder.compile()
   ```

   `after_review(state)` returns `"improve"` if `needs_improvement(state["review_decision"], state["revision_count"])`, else `"done"`. Still **no checkpointer**. Do not rely on or change LangGraph's `recursion_limit`; the limit is `needs_improvement`. Update the module docstring with the new diagram and one sentence saying the reviewer and improver are small LLM-powered specialist nodes while the router stays ordinary Python.

9. **Add the compact dev logs.** Development only (`settings.app_env == "development"`), using the same `uvicorn.error` logger as `main.py`.
   - In `answer_reviewer` (`graph.py`), one line per review. Put the reason on one line and cut it to 200 characters:

     ```
     INFO:     review: decision=improve revision_count=0 accepted=no reason=Terms like TLS handshake are not explained for a beginner.
     ```

     `accepted=yes` means the draft became `final_answer`.
   - In `main.py`, extend the existing `graph trace:` line with the last decision and the revision count:

     ```
     INFO:     graph trace: route=study review=approve revision_count=1 nodes=router->study_helper->answer_reviewer->answer_improver->answer_reviewer
     ```

   `run_graph` does not change; `nodes` already lists every node that ran, in order. Keep the `chat prompt:` line and the request/payload middleware as they are. No line may hold the API key, the reviewer or improver instruction text, or the full draft. Do not add a trace field, header, endpoint, or custom Open WebUI event to the response.

10. **Start the count and keep the response path (`main.py`).** The graph's initial state becomes `{"user_message": question, "history": history, "revision_count": 0}`. Everything after the graph stays as in Story 4.1: `label + state["final_answer"]`, then `completion_body` for `stream: false` or `event_stream(request.model, text)` for `stream: true`. Errors from the reviewer or improver (including a Groq structured-output failure) go through the existing `provider_error`, so they are normal 502 JSON errors. Do not add retries or parsing fallbacks. If the Groq model rejects structured output, stop and record it in the Implementation record.

11. **Update `docs/architecture.md`.** Edit in place, keep it short, keep the `Status:` line as it is.
    - **Chain behaviours:** add two rows, reviewer (`review_prompt`, `build_review_chain`, structured `approve`/`improve` plus reason) and improver (`improve_prompt`, `build_improve_chain`, one rewrite).
    - **Routing workflow (LangGraph)** becomes **Routing and review workflow (LangGraph)**, with:
      - the full diagram:

        ```
        START → router ──general──→ general_chat ──┐
                      └──study────→ study_helper ──┴→ answer_reviewer ──done──→ END
                                                         │        ▲
                                    improve (count = 0)  ▼        │
                                                   answer_improver (count → 1)
        ```

      - the state table with the four new fields, and `final_answer` now written by `answer_reviewer`;
      - the two new nodes' jobs;
      - the edge rules: each answer node → `answer_reviewer`; `answer_reviewer` → `END` when approved or when `revision_count` is 1; `answer_reviewer` → `answer_improver` only when the decision is `improve` and `revision_count` is 0; `answer_improver` → `answer_reviewer`;
      - the **one-revision limit**: at most one rewrite and at most two reviews per question, enforced by `needs_improvement` in code, not by the model;
      - the terms: reviewer and improver are small LLM-powered specialist nodes (specialist agents in this classroom example); the router is ordinary Python; MCP could be a future node but is not implemented;
      - the deliberate scope boundary: no other loop, retry, planner, tool, MCP, web search, RAG, human approval, persistence, extra agent, observability platform, or deployment.
    - **Message flow:** step 4 becomes "router, one answer node, then the review path"; step 6 says the answer nodes write a draft and the reviewer writes the final answer. Note that a reply can now take up to four model calls and still arrives as one piece.
    - **Development log:** add the `review:` line and the new `graph trace:` fields.
    - **Story map:** fill in Story 4.2, and add one short **Capstone outcome** sentence (see Handover).

12. **Stay in scope.** No database, persistence, checkpointer, RAG, web search, tools, MCP, human approval, planner, extra node or agent, second rewrite, retry, LLM routing, new endpoint, response field or setting, Open WebUI change, broad tests, production controls, observability platform, or deployment.

## Completion checks

Run only these, in this order. Run the app in a second terminal. The implementer cannot click in Open WebUI, so ask the participant or instructor to do checks 4 and 5 and report what they see.

1. `uv run ruff format .` then `uv run ruff check .` finish clean.
2. **Look at the graph shape** (no model call, no key printed):

   ```
   uv run python -c "from learning_companion.graph import build_graph; from learning_companion.settings import get_settings; print(build_graph(get_settings()).get_graph().draw_mermaid())"
   ```

   Expected: the Story 4.1 edges into `router`, `general_chat` and `study_helper`; solid edges from both answer nodes to `answer_reviewer`; dotted edges from `answer_reviewer` to `answer_improver` (`improve`) and to `__end__` (`done`); and one solid edge `answer_improver → answer_reviewer`. No answer node goes straight to `__end__`. Nothing else.
3. `uv run python -m learning_companion` starts without errors on port 8000. If an older instance is running there, stop it and restart.
4. **Approved directly (general).** In Open WebUI, start a **new chat** with the configured model and send:
   > Hi! How are you today?

   Expected in Open WebUI: the usual short, friendly greeting, no route label, no `Next step:` line, appearing in one piece. The chat gets a normal title.

   Expected trace:

   ```
   review: decision=approve revision_count=0 accepted=yes reason=<one short sentence>
   graph trace: route=general review=approve revision_count=0 nodes=router->general_chat->answer_reviewer
   chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
   ```

5. **Review → improve → review (study), same chat.** Send a question chosen so the first draft is likely to be dense:
   > /study Explain how HTTPS works, in one dense paragraph using the proper technical terms.

   Expected in Open WebUI: the reply starts with *Route: study helper*, then shows **only the improved answer** (the first draft is never shown): shorter sentences, technical terms briefly explained, and **exactly one** `Next step:` line at the end. It says nothing about a review. It may take noticeably longer, because up to four model calls run before it appears.

   Expected trace:

   ```
   review: decision=improve revision_count=0 accepted=no reason=<why it needs clearer wording>
   review: decision=approve revision_count=1 accepted=yes reason=<one short sentence>
   graph trace: route=study review=approve revision_count=1 nodes=router->study_helper->answer_reviewer->answer_improver->answer_reviewer
   chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
   ```

   The model decides, so results can vary. If the second review says `decision=improve revision_count=1 accepted=yes`, that is correct: the limit was reached and the draft was accepted anyway. If the first review approves directly, send the same message once more in a new chat, then record honestly what happened. Do **not** change the reviewer rule just to force an improvement.
6. **Inspect the trace.** In the app's terminal, find the lines for checks 4 and 5. Each follows a `POST /v1/chat/completions` line. Confirm: the route; each review decision; `revision_count` never above 1; `answer_improver` at most once per request; and no key, instruction text or full draft in any line. Open WebUI's background requests (title, tags, follow-ups) add their own `route=general` lines, and they should be approved; that is expected. With a system prompt set in Open WebUI, `client_messages` is one higher and `ignored=1`.
7. `git status --short` shows only the files in the table above, plus any Story 4.1 work and handout files that are still uncommitted.
8. Stop the app.

If Open WebUI is not available to the implementer, one `curl.exe` `stream: false` POST per example and one `stream: true` POST for the study example are useful smoke checks. They do **not** replace checks 4 and 5.

**Expected Open WebUI result:** in one chat, the greeting gets the usual general reply with no label, approved on the first review. The HTTPS `/study` question gets a reply that starts with *Route: study helper*, reads clearly for a beginner, and ends with one `Next step:` line, after one review → improve → review pass. Both come through `POST /v1/chat/completions` in the same JSON and SSE shapes as before.

## Handover

When done, add an **Implementation record** at the end of this file with:

- Files created or changed, noting anything different from the table above.
- The commands you actually ran, with pass or fail for each. List only what you ran.
- The graph shape from check 2 (the mermaid text is fine).
- What the participant saw in Open WebUI for checks 4 and 5 (copy the label line and the `Next step:` line exactly), and the `review:`, `graph trace:` and `chat prompt:` lines from the terminal (they hold no secrets). Say whether check 5 took the improve path on the first try. If checks 4 or 5 could not be done, say so plainly instead of reporting them as passed.
- Anything skipped or changed, and why (for example, a structured-output problem with the Groq model).

Tell the instructor that `docs/architecture.md` was updated (the two new nodes, the state additions, the full graph diagram, the edge rules, the one-revision limit, and the scope boundary) and point them to the Implementation record.

**Capstone outcome:** this is the last story. The finished Learning Companion Chatbot is: Open WebUI → the app's OpenAI-compatible `POST /v1/chat/completions` → one LangGraph workflow (a Python router picks general chat or the study helper; that LangChain chain writes a draft on Groq; a reviewer checks it; at most one improvement and one final review) → the answer in Open WebUI as normal JSON or streamed SSE. It keeps no data between requests and uses no tools, MCP, retrieval, or web search. MCP or other tools could be added later as a new node, but they are outside this course.

---

## Implementation record

**Status:** Code and docs built. Checks 1, 2, 3 and 7 pass. Checks 4 and 5 need the participant in Open WebUI and are **not yet run**, so check 6 has been done only for the `curl` requests below. Check 8 (stop the app) is not done: the app is left running on port 8000 so the participant can do checks 4 to 6.

No new branch was made and nothing was committed. Story 4.1 is still uncommitted, and this story was built on top of it on `story-3-2-visible-python-routing` (Story 3.2 is commit `797698a`). The participant can still move both stories with `git switch -c story-4-2-bounded-review-and-improve`, since uncommitted changes go along. Whether Story 4.1's Open WebUI checks were ever run could not be confirmed.

### Files created or changed

As in the table above, with these notes:

- `chain.py`: new imports (`Literal`, `BaseModel`, `Field`). Added `REVIEWER_INSTRUCTION`, `ReviewResult`, `review_prompt`, `build_review_chain` (`with_structured_output(ReviewResult)`), `IMPROVER_INSTRUCTION`, `improve_prompt`, `build_improve_chain`. The instruction texts are exactly as in steps 1 and 2. The two existing chains are unchanged.
- `graph.py`: the module docstring has the new shape. A `uvicorn.error` logger and `MAX_REVISIONS = 1` were added. `ChatState` gained `draft_answer`, `review_decision`, `review_reason` and `revision_count`, and the `final_answer` comment now says the reviewer sets it. `needs_improvement` and `after_review` are new module functions. `general_chat` and `study_helper` now return `draft_answer`. `answer_reviewer` and `answer_improver` are new nodes inside `build_graph`. The new edges are as in step 8. `router`, `next_node` and `run_graph` are unchanged, and there is still no checkpointer.
- `main.py`: the initial state has `"revision_count": 0`. The `graph trace:` line now has `review=` and `revision_count=`. The comment above the graph call was updated. Nothing else changed.
- `docs/architecture.md`: chain table (two new rows, and the intro now covers four chains); **Routing workflow** became **Routing and review workflow (LangGraph)**, with the full diagram, the state table with the new fields, the node jobs, the edge rules, the one-revision limit, the terms, and the scope boundary; message flow steps 4, 6 and 7; the dev log paragraph; the Story 4.2 entry in the story map; and a **Capstone outcome** line. The `Status:` line is unchanged.
- No new dependency or setting. Nothing in the "leave alone" list was touched.

### Commands actually run

| Command | Result |
|---|---|
| `uv run ruff format .` then `uv run ruff check .` (check 1) | pass: 25 files left unchanged; all checks passed. Run again after the docs edits: same |
| `uv run python -c "...draw_mermaid()"` (check 2) | pass: shape below |
| `uv run python -I <scratchpad>/check42.py` (offline, stub chains, no model call; not in the check list) | pass. Reviewer says `approve` → `router->study_helper->answer_reviewer`, `revision_count=0`, the first draft is final. Reviewer says `improve, approve` → one improver step, `revision_count=1`, the improved draft is final. Reviewer **always** says `improve` → still only one improver step and two reviews, `revision_count=1`, the improved draft is accepted |
| `Get-NetTCPConnection` on port 8000, then `Stop-Process` | port 8000 was held by the Story 4.1 instance (`python -m learning_companion`, started 5:10 PM); stopped |
| `uv run python -m learning_companion` (check 3) | pass: starts without errors on port 8000 |
| `curl.exe` `/health` and `/v1/models` | `{"status":"ok"}`; model `openai/gpt-oss-120b` |
| `curl.exe` `stream: false` POST, "Hi! How are you today?" (does not replace check 4) | HTTP 200: "I'm doing great, thanks! What would you like help with today?" No label, no `Next step:`. Approved directly |
| `curl.exe` `stream: false` POST, greeting turn as history + the HTTPS `/study` question (does not replace check 5) | HTTP 200; took review → improve → review on the first try; answer below |
| `curl.exe` `stream: true` POST, same study request | pass: 3 events. A `role: assistant` chunk with content starting `*Route: study helper*\n\nHTTPS`, a `finish_reason: "stop"` chunk, then `data: [DONE]`. This run also took the improve path |
| `curl.exe` POST with an Open WebUI-style title task (`### Task: ... JSON format: { "title": ... }`) | HTTP 200, content `{"title": "Warm Welcome Chat ..."}`, approved unchanged (`reason=It's a simple JSON object, which is allowed.`) |
| `curl.exe` POST with a bare `/study` | HTTP 400, the same message as Stories 3.2 and 4.1. No review line, because the router stops it first |
| `git status --short` (check 7) | pass: modified `architecture.md`, `pyproject.toml`, `chain.py`, `main.py`, `uv.lock` (`pyproject.toml` and `uv.lock` from Story 4.1); untracked `graph.py`, Stories 4.1 and 4.2, both 4.x handouts |

`pytest` was not run (this story writes no tests). Groq accepted structured output (`with_structured_output`, default method) on `openai/gpt-oss-120b` with no problem. The curl calls used the participant's `.env`, which was not read or printed.

### Graph shape (check 2)

```
__start__ --> router;
answer_improver --> answer_reviewer;
answer_reviewer -. &nbsp;done&nbsp; .-> __end__;
answer_reviewer -. &nbsp;improve&nbsp; .-> answer_improver;
general_chat --> answer_reviewer;
router -. &nbsp;general&nbsp; .-> general_chat;
router -. &nbsp;study&nbsp; .-> study_helper;
study_helper --> answer_reviewer;
```

Nodes: `router`, `general_chat`, `study_helper`, `answer_reviewer`, `answer_improver`. No answer node goes straight to `__end__`. Nothing else. (The mermaid header and style lines are left out.)

### Study answer (curl, normal path, after one improvement)

```
*Route: study helper*

HTTPS (Hypertext Transfer Protocol Secure) protects web traffic by wrapping it in a secret tunnel created with TLS (Transport Layer Security). When your browser contacts a site, it first does a quick exchange to set up the tunnel: the server sends an ID-like file (its digital certificate) that proves who it is, the browser checks that this ID is trusted, and both sides pick a secret code (a symmetric encryption key) that they will use to scramble and unscramble everything they send. After that, all data, such as the pages you view or the passwords you type, is encrypted with that secret code, so eavesdroppers can't read or change it.

*Example:* When you log into your bank, HTTPS makes sure your username and password travel across the internet in a scrambled form that only the bank's server can decode.

Next step: Learn how TLS certificates are issued and validated.
```

Label line: yes. Terms explained in plain words: yes. Exactly one `Next step:` line: yes. No mention of the review, and no claim of searching. The first draft is not shown anywhere.

### What the terminal showed (curl requests above)

```
INFO:     POST /v1/chat/completions body=111 bytes
INFO:     review: decision=approve revision_count=0 accepted=yes reason=The reply is short, friendly, and matches the general route.
INFO:     graph trace: route=general review=approve revision_count=0 nodes=router->general_chat->answer_reviewer
INFO:     chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
INFO:     POST /v1/chat/completions body=357 bytes
INFO:     review: decision=improve revision_count=0 accepted=no reason=Terms like "TLS handshake," "digital certificate," and "symmetric encryption key" aren't explained in plain language.
INFO:     review: decision=approve revision_count=1 accepted=yes reason=Meets study route: plain explanation, terms defined, and single correct Next step line.
INFO:     graph trace: route=study review=approve revision_count=1 nodes=router->study_helper->answer_reviewer->answer_improver->answer_reviewer
INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
INFO:     POST /v1/chat/completions body=354 bytes
INFO:     review: decision=improve revision_count=0 accepted=no reason=The draft uses terms like "trusted authorities" and "TLS handshake" without plain-language explanations, which a beginner needs.
INFO:     review: decision=approve revision_count=1 accepted=yes reason=Meets the study route: plain-language, all terms explained, and exactly one 'Next step:' line.
INFO:     graph trace: route=study review=approve revision_count=1 nodes=router->study_helper->answer_reviewer->answer_improver->answer_reviewer
INFO:     chat prompt: route=study roles=system,human,ai,human count=4 client_messages=3 ignored=0
INFO:     POST /v1/chat/completions body=404 bytes
INFO:     review: decision=approve revision_count=0 accepted=yes reason=It's a simple JSON object, which is allowed.
INFO:     graph trace: route=general review=approve revision_count=0 nodes=router->general_chat->answer_reviewer
INFO:     chat prompt: route=general roles=system,human count=2 client_messages=1 ignored=0
INFO:     POST /v1/chat/completions body=80 bytes
```

These are the general, normal-study, streaming-study, title-task and bare-`/study` requests, in that order. No line holds a key, instruction text, or a full draft. The payload log lines from Story 3.1 also printed each body; they are left out here. The model's curly quotes are shown as plain quotes.

### Open WebUI result (checks 4 and 5)

Not yet run. The implementer cannot use Open WebUI. The app is running on port 8000 with this story's code. Still to do, by the participant or instructor:

1. In a **new chat**, send "Hi! How are you today?". Check that the chat also gets a normal title.
2. In the **same** chat, send `/study Explain how HTTPS works, in one dense paragraph using the proper technical terms.`
3. Report both replies, the label line and the `Next step:` line, whether the study question took the improve path on the first try, and the `review:`, `graph trace:` and `chat prompt:` lines (check 6).
4. Stop the app (check 8).

### Skipped or changed

- No new branch and no commit. The story asks the participant to decide that.
- Checks 4 and 5 are not done. The curl calls show both paths, the improve cycle, the limit, the streaming shape, a title-style background request, the 400 and the trace, but they are not the Open WebUI checks.
- Check 8 is not done, on purpose, so checks 4 to 6 can be run against this code.
