# Handout 4.1 — LangGraph routing workflow

Paste this prompt into your coding assistant from the capstone repository:

---

Create `docs/stories/story-4-1-langgraph-routing-workflow.md`. Create the story only; do **not** implement it, install dependencies, or change application code now. Read `docs/config.yaml` if present, `docs/architecture.md`, Stories 1.1–3.2, existing LangChain chains, `.env.example`, and the OpenAI-compatible chat adapter first. Preserve the working Open WebUI connection, API endpoints, request/response shape, Grok configuration, normal JSON replies, and streaming SSE behavior.

Write short, plain-English sections in this exact order: **Purpose**, **What this story implements in plain English**, **Prerequisites**, **Work to do**, **Completion checks**, and **Handover**. The plain-English functionality section is mandatory: explain in 3–5 short bullets what happens to a question after it enters the chatbot, without assuming the participant knows graph terminology.

This story must replace only the internal ordinary-Python route from Story 3.2 with one small LangGraph workflow. It must reuse the existing general-chat and study-helper LangChain chains. It must not replace the FastAPI service, OpenAI-compatible endpoint, Open WebUI client, Grok settings, or message-history conversion. Do not create a second application or chat route.

Define a minimal typed graph state with: current user message, current conversation messages, selected route, and final answer. Explain these state fields in plain English in the story before implementation work begins.

Require these three nodes and only these responsibilities:

1. **Router node** — ordinary Python logic, not an agent. It preserves the existing `/study` rule and writes `general` or `study` into state.
2. **General-chat node** — calls the existing general-chat LangChain chain and writes the final answer.
3. **Study-helper node** — calls the existing study-helper LangChain chain and writes the final answer.

Require explicit graph edges: `START → router`; conditional routing from router to general-chat or study-helper; and an edge from each answer node to `END`. Preserve exactly the existing `/study` behaviour while making the route, state, nodes, and edges visible in code. This story has no reviewer, improver, loop, or retry; Story 4.2 adds the bounded review path.

Make the terminology precise in the story: a node is a focused piece of work, not automatically an agent. The router is ordinary application logic. The two Grok-powered answer nodes may be described as small specialist behaviours. An MCP tool call could be placed inside a future node, but MCP is explicitly not implemented in this course story.

The graph output must continue through the existing OpenAI-compatible normal and streaming response adapter so participants see the final answer in Open WebUI. For classroom inspection, use compact safe logs or a development-only trace that reports route and node sequence. Do not expose API keys, full hidden prompts, or a custom Open WebUI response format. Update `docs/architecture.md` with the graph diagram, state fields, node responsibilities, edge rules, and what remains out of scope.

Keep checks lightweight: format/lint; run one general-chat question and one `/study` question through the existing Open WebUI chat; confirm both final answers reach Open WebUI; and inspect the compact trace. Do not add databases, persistence, RAG, web search, tool execution, MCP, human approval, review steps, loops, additional agents, broad test suites, security programmes, observability platforms, or deployment work.

The story must name files it changes, commands actually run, the expected Open WebUI result and trace for both paths, and what Story 4.2 will extend. After creating the story, report its path only.