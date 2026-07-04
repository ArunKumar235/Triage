from contextlib import asynccontextmanager
from fastapi import FastAPI

from triage.config import get_settings
from triage.api.deps import init_engine, get_engine
from triage.api.routes import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # app.state.kafka_producer = producer
    # producer = request.app.state.kafka_producer
    init_engine(get_settings())
    try:
        yield
    finally:
        engine = get_engine()
        if engine is not None:
            await engine.dispose()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title = settings.app_name, lifespan = lifespan)

    app.include_router(health.router)
    
    return app

app = create_app()