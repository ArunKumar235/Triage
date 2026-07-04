from contextlib import asynccontextmanager
from fastapi import FastAPI

from triage.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # app.state.kafka_producer = producer
    # producer = request.app.state.kafka_producer
    try:
        yield
    finally:
        pass

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title = settings.app_name, lifespan = lifespan)

    return app

app = create_app()