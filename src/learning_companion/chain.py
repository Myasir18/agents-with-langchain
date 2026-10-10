from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from learning_companion.schemas import ChatMessage
from learning_companion.settings import Settings

# Application instructions. Fixed text owned by the app. User text never goes
# in here; it enters the prompt only through history and {question} below.
LEARNING_COMPANION_INSTRUCTION = (
    "You are the Learning Companion, a friendly, plain-spoken study helper. "
    "Give short, clear answers a beginner can follow. "
    "If the question is vague, ask one short follow-up question."
)

# At most this many earlier chat messages (about five turns) reach the model.
MAX_HISTORY_MESSAGES = 10

prompt = ChatPromptTemplate.from_messages(
    [
        # Part one: the app's own instruction (system message, no variables).
        SystemMessage(content=LEARNING_COMPANION_INSTRUCTION),
        # Part two: earlier user and assistant messages from this request.
        MessagesPlaceholder("history"),
        # Part three: the current user message (human message).
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)


def to_history(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Earlier client messages as LangChain messages, oldest first.

    Only plain-text user and assistant messages are kept. Client system
    messages, other roles, and non-text content are skipped. Only the last
    MAX_HISTORY_MESSAGES are returned.
    """
    history: list[BaseMessage] = []
    for message in messages:
        if not isinstance(message.content, str) or not message.content.strip():
            continue
        if message.role == "user":
            history.append(HumanMessage(content=message.content))
        elif message.role == "assistant":
            history.append(AIMessage(content=message.content))
    return history[-MAX_HISTORY_MESSAGES:]


def describe_prompt(inputs: dict) -> str:
    """One short line for development logs: message roles in order and count.

    Never includes message text, so the hidden instruction, the user's
    messages, and settings such as the API key cannot appear in it.
    """
    messages = prompt.format_messages(**inputs)
    roles = ",".join(message.type for message in messages)
    return f"roles={roles} count={len(messages)}"


def build_chain(settings: Settings):
    """Prompt -> Groq chat model -> text output.

    Called per chat request, not at startup, so the app can start without a
    real API key.
    """
    model = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base_url,
    )
    return prompt | model | StrOutputParser()


# Study-helper instructions. Fixed text owned by the app, like the one above.
STUDY_HELPER_INSTRUCTION = (
    "You are the Learning Companion's study helper. "
    "Explain the beginner technical concept the learner asks about in plain "
    "language, in a few short sentences. "
    "Add one small example only if it makes the idea clearer. "
    "End with exactly one small suggested next learning step, on its own line "
    'starting with "Next step:". '
    "If you are not sure about something, say so plainly."
)

study_prompt = ChatPromptTemplate.from_messages(
    [
        # Part one: the study helper's own instruction (system message).
        SystemMessage(content=STUDY_HELPER_INSTRUCTION),
        # Part two: earlier user and assistant messages from this request.
        MessagesPlaceholder("history"),
        # Part three: the current user message (human message).
        HumanMessagePromptTemplate.from_template("{question}"),
    ]
)


def build_study_chain(settings: Settings):
    """Study-helper prompt -> Groq chat model -> text output.

    The study-helper node in graph.py uses it for messages that start with
    /study.
    """
    model = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base_url,
    )
    return study_prompt | model | StrOutputParser()


# Answer reviewer's fixed classroom rule. Owned by the app, like the
# instructions above. The draft enters only through {draft} below.
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


class ReviewResult(BaseModel):
    """The reviewer's structured decision."""

    decision: Literal["approve", "improve"]
    reason: str = Field(description="One short plain-English sentence.")


review_prompt = ChatPromptTemplate.from_messages(
    [
        # Part one: the reviewer's fixed rule (system message).
        SystemMessage(content=REVIEWER_INSTRUCTION),
        # Part two: the route and the draft to review (human message).
        HumanMessagePromptTemplate.from_template(
            "Route: {route}\n\nDraft answer:\n{draft}"
        ),
    ]
)


def build_review_chain(settings: Settings):
    """Reviewer prompt -> Groq chat model -> ReviewResult.

    The answer-reviewer node in graph.py uses it. No history, no tools.
    """
    model = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base_url,
    )
    return review_prompt | model.with_structured_output(ReviewResult)


# Answer improver's instruction. Fixed text owned by the app.
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

improve_prompt = ChatPromptTemplate.from_messages(
    [
        # Part one: the improver's fixed instruction (system message).
        SystemMessage(content=IMPROVER_INSTRUCTION),
        # Part two: the reviewer's note and the draft (human message).
        HumanMessagePromptTemplate.from_template(
            "Reviewer note: {reason}\n\nDraft answer:\n{draft}"
        ),
    ]
)


def build_improve_chain(settings: Settings):
    """Improver prompt -> Groq chat model -> text output.

    The answer-improver node in graph.py uses it, at most once per request.
    """
    model = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base_url,
    )
    return improve_prompt | model | StrOutputParser()
