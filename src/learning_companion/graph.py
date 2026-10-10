"""The app's one LangGraph workflow: a router, one answer node, then a
bounded review.

START -> router -> general_chat or study_helper -> answer_reviewer
answer_reviewer -> END, or -> answer_improver -> answer_reviewer (once only)

A node is one focused piece of work, not automatically an agent. The router
is ordinary application logic (a fixed text rule). The two answer nodes are
small specialist behaviours that each call an existing LangChain chain. The
reviewer and improver are small LLM-powered specialist nodes; Python code,
not the model, limits the improver to one rewrite.
"""

import logging
from typing import Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from learning_companion.chain import (
    build_chain,
    build_improve_chain,
    build_review_chain,
    build_study_chain,
)
from learning_companion.settings import Settings

# The same logger as main.py, so review lines show up in the app's terminal.
logger = logging.getLogger("uvicorn.error")

# At most this many rewrites per question.
MAX_REVISIONS = 1


class ChatState(TypedDict):
    """What the workflow keeps for one request. Nothing is saved afterwards."""

    # The current question: the latest user message's text.
    user_message: str
    # Earlier messages of this chat, already converted by to_history.
    history: list[BaseMessage]
    # Which answer node runs: "general" or "study". Set by the router.
    route: Literal["general", "study"]
    # The current answer: the answer node's, then the improver's if it runs.
    draft_answer: str
    # The reviewer's latest verdict.
    review_decision: Literal["approve", "improve"]
    # The reviewer's one short reason; the improver's note for the rewrite.
    review_reason: str
    # How many rewrites happened: 0 or 1. The app starts it at 0.
    revision_count: int
    # The accepted answer, before the app adds the study label. Set by the
    # reviewer.
    final_answer: str


class EmptyStudyQuestion(Exception):
    """A message that is only /study, with no question after it."""


def router(state: ChatState) -> dict:
    """Router node: ordinary Python, no model call.

    A message whose first word is /study goes to the study helper, with the
    marker removed. Everything else goes to general chat unchanged.
    """
    words = state["user_message"].split(maxsplit=1)
    if words[0] == "/study":
        rest = words[1].strip() if len(words) > 1 else ""
        if not rest:
            raise EmptyStudyQuestion(
                "Add a question after /study, for example: /study What is an API?"
            )
        return {"route": "study", "user_message": rest}
    return {"route": "general"}


def next_node(state: ChatState) -> str:
    """The conditional edge after the router: read the route it wrote."""
    return state["route"]


def needs_improvement(decision: str, revision_count: int) -> bool:
    """The one-revision limit: improve only a first draft the reviewer
    asked to improve. After one rewrite the draft is always accepted."""
    return decision == "improve" and revision_count < MAX_REVISIONS


def after_review(state: ChatState) -> str:
    """The conditional edge after the reviewer: one rewrite, or done."""
    if needs_improvement(state["review_decision"], state["revision_count"]):
        return "improve"
    return "done"


def build_graph(settings: Settings):
    """Build and compile the workflow.

    Called per chat request, like the chains, so the app can start without
    a real API key. No checkpointer: nothing is stored between requests.
    """

    async def general_chat(state: ChatState) -> dict:
        """General-chat node: calls the existing general-chat chain."""
        answer = await build_chain(settings).ainvoke(
            {"history": state["history"], "question": state["user_message"]}
        )
        return {"draft_answer": answer}

    async def study_helper(state: ChatState) -> dict:
        """Study-helper node: calls the existing study-helper chain."""
        answer = await build_study_chain(settings).ainvoke(
            {"history": state["history"], "question": state["user_message"]}
        )
        return {"draft_answer": answer}

    async def answer_reviewer(state: ChatState) -> dict:
        """Answer-reviewer node: LLM-powered specialist, one structured check.

        Writes final_answer when the draft is approved, or when the
        one-revision limit is reached, whatever the model says.
        """
        result = await build_review_chain(settings).ainvoke(
            {"route": state["route"], "draft": state["draft_answer"]}
        )
        update = {"review_decision": result.decision, "review_reason": result.reason}
        accepted = not needs_improvement(result.decision, state["revision_count"])
        if accepted:
            update["final_answer"] = state["draft_answer"]
        if settings.app_env == "development":
            reason = " ".join(result.reason.split())[:200]
            logger.info(
                "review: decision=%s revision_count=%d accepted=%s reason=%s",
                result.decision,
                state["revision_count"],
                "yes" if accepted else "no",
                reason,
            )
        return update

    async def answer_improver(state: ChatState) -> dict:
        """Answer-improver node: LLM-powered specialist, rewrites the draft
        once using the reviewer's reason. No tools, history, or routing."""
        improved = await build_improve_chain(settings).ainvoke(
            {"reason": state["review_reason"], "draft": state["draft_answer"]}
        )
        return {"draft_answer": improved, "revision_count": state["revision_count"] + 1}

    builder = StateGraph(ChatState)
    builder.add_node("router", router)
    builder.add_node("general_chat", general_chat)
    builder.add_node("study_helper", study_helper)
    builder.add_node("answer_reviewer", answer_reviewer)
    builder.add_node("answer_improver", answer_improver)
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        next_node,
        {"general": "general_chat", "study": "study_helper"},
    )
    builder.add_edge("general_chat", "answer_reviewer")
    builder.add_edge("study_helper", "answer_reviewer")
    builder.add_conditional_edges(
        "answer_reviewer",
        after_review,  # "improve" only when needs_improvement(...) is true
        {"improve": "answer_improver", "done": END},
    )
    builder.add_edge("answer_improver", "answer_reviewer")
    return builder.compile()


async def run_graph(graph, state: dict) -> tuple[dict, list[str]]:
    """Run the workflow once: the final state and the nodes that ran, in order."""
    nodes: list[str] = []
    final_state = state
    async for mode, chunk in graph.astream(state, stream_mode=["updates", "values"]):
        if mode == "updates":
            nodes.extend(chunk)
        else:
            final_state = chunk
    return final_state, nodes
