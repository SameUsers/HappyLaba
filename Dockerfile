FROM python:3.12-slim

WORKDIR /happy_laba

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --no-dev --no-install-project

COPY . .

RUN uv sync --no-dev

CMD ["uv", "run", "python", "main.py"]