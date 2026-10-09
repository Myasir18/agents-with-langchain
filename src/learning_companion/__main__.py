import uvicorn

from learning_companion.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("learning_companion.main:app", host=settings.host, port=settings.port)
