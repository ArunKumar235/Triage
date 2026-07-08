from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

from triage.config import get_settings
from triage.api.deps import init_engine, get_engine
from triage.api.routes import health
from triage.api.routes import testables
from triage.api.routes import teams
from triage.api.routes import team_members
from triage.core.kafka.producer import close_producer, get_producer
from triage.core.kafka.consumer_assignment import consume_assignment_events
from triage.core.kafka.consumer_rebalancing import consume_rebalancing_events
from triage.core.kafka.consumer_notification import consume_notification_events

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine(get_settings())
    get_producer(get_settings())

    # Signal the consumer loops to drain and exit on app shutdown.
    stop_event = asyncio.Event()
    consumer_tasks = [
        asyncio.create_task(consume_assignment_events(stop_event), name="kafka-consumer-assignment"),
        asyncio.create_task(consume_rebalancing_events(stop_event), name="kafka-consumer-rebalancing"),
        asyncio.create_task(consume_notification_events(stop_event), name="kafka-consumer-notification"),
    ]

    try:
        yield
    finally:
        # Tell the consumer loops to stop and wait briefly for them to drain.
        stop_event.set()
        try:
            await asyncio.wait_for(
                asyncio.gather(*consumer_tasks, return_exceptions=True),
                timeout=10,
            )
        except asyncio.TimeoutError:
            for task in consumer_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*consumer_tasks, return_exceptions=True)

        engine = get_engine()
        if engine is not None:
            await engine.dispose()
        await close_producer()

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title = settings.app_name, lifespan = lifespan)

    app.include_router(health.router)
    app.include_router(testables.router)
    app.include_router(teams.router)
    app.include_router(team_members.router)

    return app

app = create_app()