from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_groq import ChatGroq

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

    The chat route uses it for messages that start with /study.
    """
    model = ChatGroq(
        model=settings.groq_model_name,
        api_key=settings.groq_api_key,
        base_url=settings.groq_api_base_url,
    )
    return study_prompt | model | StrOutputParser()
