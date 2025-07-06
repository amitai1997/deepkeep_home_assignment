# Chat Gateway

Minimal FastAPI service used for the home assignment. The project is split into
`src/`, `tests/`, `docs/`, and `infra/` following the project plan.

## Quick start

```bash
docker build -f infra/Dockerfile -t chat-gw .
docker run -p 8000:8000 -e OPENAI_API_KEY=dummy chat-gw
```

## Development

Install dependencies with Poetry and run the app:

```bash
poetry install
poetry run uvicorn src.main:app --reload
```

