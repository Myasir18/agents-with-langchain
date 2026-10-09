# Handout 3.2 — Visible Python routing between the two chains

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-3-2-visible-python-routing.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Stories 1.1–3.1, existing code, both LangChain chains, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve the working Open WebUI connection, endpoints, Grok settings, message-history handling, and normal JSON/SSE response shapes.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets how an ordinary question and a `/study` question take different paths, without calling this a LangGraph workflow or autonomous routing.

This story makes the two existing chains reachable through the same Open WebUI chat endpoint. Implement one deliberately simple, visible Python rule: if the latest user message begins with `/study`, select the study-helper chain; otherwise select the existing general-chat chain. Strip only the leading `/study` marker before passing the current question to the study-helper. Keep all other current request messages as history under the rules established in Story 2.2.

Record the selected `general` or `study` route through a compact development log or a safe development-only trace. When practical without breaking the OpenAI-compatible response shape, include a short classroom-readable route label in the answer text. Do not create custom response fields or Open WebUI plugins. The purpose is for participants to see the ordinary `if/else` that Session 4 will later replace internally with an explicit LangGraph route.

Require the selected chain to work through the existing normal and streaming response adapter, so both paths are used from the participant’s existing Open WebUI conversation. Update `docs/architecture.md` with the `/study` rule, the selected-chain path, and the boundary: this is deterministic application routing, not LLM classification, LangGraph, or multi-agent orchestration.

Keep completion checks lightweight: format/lint, one general-chat message in Open WebUI, one `/study Explain what an API is` message in Open WebUI, and inspection of the route log or trace. Confirm that both replies come through the same endpoint and that the study-helper response includes a clear explanation and one next step. Do not add LLM routing, additional specialists, review steps, loops, broad tests, or production controls.

The story must name the files it changes, commands actually run, expected Open WebUI results for both routes, and what Story 4.1 will extend. After creating the story, report its path only.