FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl curl \
    && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml backend/poetry.lock* /app/
RUN pip install --no-cache-dir poetry \
    && poetry install --no-root
COPY backend/app /app/app
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
EXPOSE 443
CMD ["/app/entrypoint.sh"]
