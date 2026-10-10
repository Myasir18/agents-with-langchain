# Handout 4.2 — Bounded answer review and improvement

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-4-2-bounded-review-and-improve.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Stories 1.1–4.1, the existing LangGraph state and nodes, both LangChain answer chains, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve the working Open WebUI connection, API endpoints, request/response shape, Grok configuration, normal JSON replies, streaming SSE behavior, and LangGraph routing path.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets that the chatbot can check a draft once, improve it once when necessary, and then stop. Do not imply unlimited self-correction or autonomous work.

This story extends the existing three-node LangGraph; it does not rebuild it. Add only two new Grok-powered specialist nodes:

1. **Answer-reviewer node** — receives the draft answer and selected route. Against a short fixed classroom rule, it decides whether the draft is clear and appropriate for the general-chat or study-helper role. It produces a structured `approve` or `improve` decision and one short plain-English reason.
2. **Answer-improver node** — receives the draft and reviewer reason, rewrites the answer once, and increments a revision count. It does not use tools, browse, retrieve information, make a plan, or make another routing choice.

Extend the typed graph state only with `draft_answer`, `review_decision`, `review_reason`, `revision_count`, and `final_answer`. Explain each new field in plain English before implementation work begins. Reuse the existing router and answer nodes, changing them only as needed to write a draft rather than final answer.

Require these bounded edges: each answer node goes to reviewer; an approved draft goes to `END`; an improvement-needed draft goes to improver only when `revision_count` is zero; the improver returns to reviewer for one final approval. Once `revision_count` is one, the reviewer must accept the current draft as final and end. This makes a visible cycle—reviewer → improver → reviewer—while enforcing a maximum of one improvement. There must be no other loop, retry, planner, tool, or open-ended agent behaviour.

Keep the terminology precise: the reviewer and improver are small LLM-powered specialist nodes, which may be called specialist agents for this classroom example. The router remains ordinary Python logic, not an agent. The workflow still has no MCP tool call; an MCP call can be a future node, but is explicitly outside this story.

Route the graph’s final answer through the existing OpenAI-compatible normal and streaming adapter so Open WebUI displays the result as before. Add compact safe logs or a development-only trace for route, reviewer decision, revision count, and node sequence. Do not expose API keys, full hidden prompts, or custom Open WebUI events. Update `docs/architecture.md` with the two new nodes, state additions, full graph diagram, edge rules, one-revision limit, and deliberate scope boundary.

Keep completion checks lightweight: format/lint; use the existing Open WebUI chat for one ordinary question that the reviewer approves directly; use one `/study` question chosen to benefit from clearer wording and inspect the review → improve → review path; confirm the final answer appears in Open WebUI; and inspect the compact trace. Do not add databases, persistence, RAG, web search, tools, MCP, human approval, additional agents, broad test suites, production controls, observability platforms, or deployment work.

The story must name files it changes, commands actually run, expected Open WebUI results and traces for both examples, and the final capstone outcome. After creating the story, report its path only.