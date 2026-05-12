FROM python:3.13-slim

WORKDIR /code

RUN apt-get update && \ 
    apt-get install -y --no-install-recommends gcc libpq-dev default-libmysqlclient-dev pkg-config && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

RUN python -m spacy download es_core_news_sm
RUN python -m spacy download en_core_web_sm

# Se copia todo el proyecto
COPY . .

# Comando para arrancar la api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]