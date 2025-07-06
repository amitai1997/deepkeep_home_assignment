# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app

# Install pip and wheel
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy dependency information
COPY pyproject.toml ./

# Extract dependencies manually from pyproject.toml
RUN pip install --no-cache-dir tomlkit \
    && python -c "import tomlkit; f = open('pyproject.toml'); data = tomlkit.parse(f.read()); f.close(); deps = data['project']['dependencies']; print('\n'.join(deps))" > requirements.txt \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --find-links=/wheels -r requirements.txt
COPY src ./src

# Set environment variables for running the app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0"]
