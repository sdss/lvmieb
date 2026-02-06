FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

LABEL org.opencontainers.image.authors="Jose Sanchez-Gallego, gallegoj@uw.edu"
LABEL org.opencontainers.image.source=https://github.com/sdss/lvmieb

WORKDIR /opt

COPY . lvmieb

ENV UV_COMPILE_BYTECODE=1
ENV ENV UV_LINK_MODE=copy

# Sync the project
RUN cd lvmieb && uv sync --frozen --no-cache

CMD ["/opt/lvmieb/.venv/bin/lvmieb", "actor", "start", "--debug"]
