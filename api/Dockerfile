FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app.py ./app.py
COPY src/ ./src/
COPY mlruns/ ./mlruns/

RUN uv sync --no-dev

ENV ENV=staging
ENV MLFLOW_SERVER=file:///app/mlruns
ENV MLFLOW_REGISTRY_NAME=purchase_predict
ENV PORT=80
EXPOSE 80

CMD ["sh", "-c", "uv run gunicorn app:app -b 0.0.0.0:${PORT:-80} -w ${WEB_CONCURRENCY:-4}"]
