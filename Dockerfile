# syntax=docker/dockerfile:1
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONTAINER_PORT=8000

WORKDIR /app

COPY requirements.txt .
# Reuse downloaded wheels between local BuildKit builds. This cache is a build
# artifact only; it is not copied into the final image or the app's data volume.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:${CONTAINER_PORT}"]
