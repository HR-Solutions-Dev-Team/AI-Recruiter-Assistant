FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* frontend/yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY frontend/ .
RUN npm run build

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
COPY --from=frontend-build /frontend/dist /app/static
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
EXPOSE 443
CMD ["/app/entrypoint.sh"]
