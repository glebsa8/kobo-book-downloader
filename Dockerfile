# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.12.6 AS uv
FROM python:3.13.12-slim-bookworm

COPY --from=uv /uv /uvx /bin/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    XDG_CONFIG_HOME=/config

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE.md ./
COPY kobo_book_downloader ./kobo_book_downloader

RUN uv sync --locked --no-dev --no-editable \
    && mkdir -p /books /config

VOLUME ["/books", "/config"]

ENTRYPOINT ["kobo-book-downloader"]
CMD ["--help"]
