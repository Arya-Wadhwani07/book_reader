FROM python:3.13-slim AS build
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN python -m venv /app/.venv && /app/.venv/bin/python -m pip install -r requirements.txt
RUN TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken /app/.venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

FROM python:3.13-slim
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TMPDIR=/app/.cache/tmp
COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/.cache/tiktoken /app/.cache/tiktoken
COPY src ./src
COPY static ./static
COPY corpus ./corpus
COPY scripts ./scripts
COPY requirements.txt .
RUN useradd --uid 10001 --no-create-home appuser && mkdir -p /app/.cache/tmp /app/.data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["sh", "-c", "exec /app/.venv/bin/python -m uvicorn src.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8080}"]
