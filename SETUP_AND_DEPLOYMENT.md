# Setup and deployment

This covers what you need to get the project running locally. I use `uv` for Python dependency management and Docker Compose for the infrastructure services.

## Prerequisites

- Python 3.12 (the version is pinned in `.python-version`)
- Docker and Docker Compose
- `uv` installed (`pip install uv` or via the official installer)

## Installing dependencies

```bash
uv sync
```

This installs everything from `uv.lock`. Run this once after cloning, and again whenever the lockfile changes (e.g. after pulling changes that added new packages).

## Starting the infrastructure

Triage depends on Kafka for event handling and Mailpit for local email testing. Both are defined in `docker-compose.yml`. Kafka runs in KRaft mode here, so there's no separate Zookeeper container to worry about — it's just the one service.

```bash
docker-compose up -d
```

Once that's up, Kafka will be available on `localhost:9092` and the Mailpit web UI at `http://localhost:8025`. Any emails the notification module sends in dev mode will show up there.

## Environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

The variables you'll need to set:

- `DATABASE_URL` — connection string to your PostgreSQL instance. The default in `.env.example` uses `asyncpg` as the driver, so make sure that's installed.
- `KAFKA_BOOTSTRAP_SERVERS` — `localhost:9092` if you're using the Docker setup
- `VECTOR_STORE_PATH` — path where the local vector store is persisted. I have this set to `./vector_store`, which is already in `.gitignore`.
- `ORCHESTRATOR_MODEL` — the Ollama model used for reasoning generation. I'm using `gpt-oss:120b-cloud`.
- `EMBEDDING_MODEL` — the model used to generate embeddings for semantic search. I'm using `nomic-embed-text:v1.5`.
- `WEBHOOK_SHARED_SECRET` — used to verify incoming webhook payloads.

The Kafka topic names and their dead-letter queue counterparts are pre-filled in `.env.example` and shouldn't need changing for local development.

SMTP settings point to Mailpit by default (`localhost:1025`), so you don't need real credentials locally.

Everything else in `.env.example` has sensible defaults for local development.

## LangSmith tracing (optional)

If you have a LangSmith account, you can enable tracing to monitor the LLM calls and graph execution. Set the following environment variables in your `.env` file:

- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_API_KEY=<your_langsmith_api_key>`
- `LANGCHAIN_PROJECT=Triage` (or any project name you prefer)

These variables are already present in `.env.example` with placeholder values. When enabled, you'll be able to view traces at https://smith.langchain.com.

## Ollama setup

Since this project runs models locally via Ollama, you'll need Ollama installed and the two models pulled before the app will work.

Install Ollama from [ollama.com](https://ollama.com), then pull the models:

```bash
ollama pull nomic-embed-text:v1.5
ollama pull gpt-oss:120b-cloud
```

`nomic-embed-text:v1.5` handles all the embedding generation for the vector store. `gpt-oss:120b-cloud` is the orchestrator model — the one that reads the final ranking and writes the assignment reasoning.

## Database setup

I use Alembic for schema migrations. Before running the app for the first time, apply all migrations:

```bash
uv run alembic upgrade head
```

If you add a new model or change an existing one, generate a migration with:

```bash
uv run alembic revision --autogenerate -m "describe your change here"
```

## Running the app

```bash
uv run uvicorn triage.main:app --reload
```

The API will be at `http://localhost:8000`. The interactive docs are at `http://localhost:8000/docs` — I keep that open while working on new endpoints since FastAPI generates them automatically.
