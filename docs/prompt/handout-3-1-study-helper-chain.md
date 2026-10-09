# Handout 3.1 — Study-helper LangChain chain

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-3-1-study-helper-chain.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Stories 1.1–2.2, existing code, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve the existing endpoints, Grok settings, request/response behavior, Open WebUI connection, and conversation-message handling.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets what the participant can now ask the chatbot to do, without calling ordinary routing an autonomous agent.

This story adds one study-helper LangChain behaviour to the same Learning Companion Chatbot. Keep the existing general-chat chain unchanged for greetings and ordinary conversation. Add a separately named study-helper chain that explains beginner technical concepts in plain language and ends with one small suggested next learning step. Both chains use the same configured Grok model, the same current request conversation history, the same OpenAI-compatible chat endpoint, and the same Open WebUI conversation. Do not create a second application, endpoint, model provider, UI, database, retrieval system, MCP server, tool call, LangGraph workflow, or autonomous agent.

Require the existing general-chat chain to remain untouched and add one separately named study-helper prompt → Grok model → text-output chain. The study-helper instruction should ask for a concise explanation, a small example where useful, and one next step; it must not claim to perform research, browse, retrieve course data, or guarantee correctness. Keep stable application instructions separate from user content.

Do not change the active application route yet. Provide a small project-local way for the implementer to invoke the study-helper chain during development without changing the Open WebUI endpoint’s existing general-chat behaviour. Story 3.2 adds the visible `/study` route rule.

Update `docs/architecture.md` with the two available chain behaviours and their responsibilities. Make clear that this story creates the study-helper capability only; selection between chains is the next story.

Keep completion checks lightweight: format/lint, one existing general-chat Open WebUI message to confirm it remains unchanged, and one focused local invocation of the study-helper chain. Confirm that the study-helper answer contains a plain explanation and one next step. Do not add routing, LLM-based classification, more specialists, loops, review steps, broad tests, or production controls.

The story must name the files it changes, commands actually run, expected results, and what Story 3.2 will extend. After creating the story, report its path only.