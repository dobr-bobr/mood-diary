FROM python:3.11.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"

RUN pip install poetry==2.1.2

RUN poetry config virtualenvs.in-project true

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN poetry install --no-interaction --no-ansi

COPY . /app/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
EXPOSE 8501
