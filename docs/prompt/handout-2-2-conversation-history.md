# Handout 2.2 — Conversation history from Open WebUI

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-2-2-conversation-history.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Stories 1.1 and 2.1, existing code, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve the working endpoints, Grok configuration, LangChain prompt template, normal JSON/SSE behavior, and Open WebUI connection.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets how a follow-up question can use earlier chat messages, without framework jargon.

This story adds only short, request-provided conversation history to the existing prompt template. Open WebUI already sends the messages for the active chat. The application must convert supported prior `user` and `assistant` messages into LangChain messages in their original order and place them between the application-owned system instruction and the latest user message. Use a LangChain message placeholder rather than assembling an ad-hoc prompt string.

Keep the boundary explicit: this is not database-backed or cross-session memory. The application saves nothing after a request is complete. It uses only a small, documented maximum number of recent messages provided by the current Open WebUI request. Ignore unsupported message content or roles safely; a request-supplied `system` message must never replace the application’s stable instruction. Preserve the existing request and response shapes and use the same prompt → Grok model → text-output chain for normal and streaming replies.

Add only a compact development log or inspectable helper showing message roles and message count. Never log API keys, full hidden application instructions, or large message bodies. Update `docs/architecture.md` with the request-provided history flow, message limit, and no-persistence boundary. Do not add a database, persistent memory, RAG, tools, MCP, routing, LangGraph, a new endpoint, or a new UI.

Keep completion checks lightweight: format/lint, then use the existing Open WebUI chat for a prepared first question followed by a question whose answer depends on it. Confirm the expected message-role sequence and that the follow-up answer uses the earlier context. Do not add an evaluation harness, broad test suite, or production memory features.

The story must name the files it changes, commands actually run, expected two-turn Open WebUI result, and what Story 3.1 will extend. After creating the story, report its path only.