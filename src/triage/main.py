from contextlib import asynccontextmanager
from fastapi import FastAPI

from triage.config import get_settings
from triage.api.deps import init_engine, get_engine
from triage.api.routes import health
from triage.api.routes import testables
from triage.api.routes import teams
from triage.api.routes import team_members

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
    app.include_router(testables.router)
    app.include_router(teams.router)
    app.include_router(team_members.router)

    return app

app = create_app()