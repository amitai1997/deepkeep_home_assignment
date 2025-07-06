# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml ./
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --find-links=/wheels -r requirements.txt
COPY src ./src
CMD ["python", "-m", "src.main"]
