"""Development only: ask the study-helper chain one question.

uv run python -m learning_companion.try_study "What is an API?"

Not used by the app or its routes. Prints only the answer text.
"""

import sys

from learning_companion.chain import build_study_chain
from learning_companion.settings import get_settings


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Usage: uv run python -m learning_companion.try_study "<question>"')
        return 2

    settings = get_settings()
    missing = settings.missing_setting()
    if missing:
        print(f"{missing} is not set. Add it to .env and try again.")
        return 1

    chain = build_study_chain(settings)
    try:
        answer = chain.invoke({"history": [], "question": question})
    except Exception as exc:
        # Only the error type: the message could echo request details.
        message = f"Groq did not accept the request ({type(exc).__name__})."
        raise SystemExit(message) from exc
    # Model text can hold characters the Windows console code page cannot show.
    sys.stdout.reconfigure(encoding="utf-8")
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
