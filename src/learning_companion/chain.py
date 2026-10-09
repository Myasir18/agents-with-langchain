from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from learning_companion.settings import Settings

# Application instructions. User text never goes in here; it is passed in
# separately as the {question} variable.
LEARNING_COMPANION_INSTRUCTION = (
    "You are the Learning Companion, a friendly, plain-spoken study helper. "
    "Give short, clear answers a beginner can follow. "
    "If the question is vague, ask one short follow-up question."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", LEARNING_COMPANION_INSTRUCTION),
        ("human", "{question}"),
    ]
)


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
