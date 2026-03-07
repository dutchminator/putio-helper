FROM python:3.10.7-alpine
LABEL Maintainer="Sebastiaan Candel <mail@sebastiaancandel.nl>"
LABEL org.opencontainers.image.source=https://github.com/dutchminator/sonarr-putio-helper

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install dependencies
COPY pyproject.toml uv.lock /app/
RUN cd /app && uv sync --no-dev --no-editable

# Copy logic
COPY src/sonarr_putio_helper.py /app/src/sonarr_putio_helper.py
COPY src/init.sh /app/init.sh

# What user are we running as
RUN echo $(id)

# Start via init.sh
ENTRYPOINT sh app/init.sh
