# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sonarr Putio Helper is a Python application that monitors a local directory for `.torrent`/`.magnet` files and uploads them to Put.io for download. It runs as a Docker container with configurable user/group IDs for proper file permissions.

## Architecture

Single-file Python app (`src/sonarr_putio_helper.py`) with a linear startup flow:
1. Collect environment variables (`collect_environment`)
2. Verify local filesystem paths (`verify_filesystem`)
3. Authenticate with Put.io API (`connect_putio`)
4. Resolve/create target folder on Put.io (`get_or_create_putio_folder`)
5. Start a watchdog `Observer` that triggers Put.io transfers on file creation events
6. Run polling loop until interrupted

Uses Go-style `(result, error)` tuple returns throughout.

Key dependencies: `putiopy` (Put.io API client), `watchdog` (filesystem event monitoring). Dev tooling: `ruff` (linting and formatting).

## Required Environment Variables

- `PUTIO_OAUTH_TOKEN` - Put.io OAuth token
- `TORRENT_PATH` - Local path to watch for torrent/magnet files
- `PUTIO_PATH` - Target folder path on Put.io
- `TORRENT_POLL_DELAY` - Poll interval in seconds (default: 1)
- `PUID`/`PGID` - Container user/group IDs (default: 1337/1338)

## Commands

### Build Docker image
```bash
docker build -t putio-helper .
```

### Install dependencies locally
```bash
uv sync        # production deps only
uv sync --dev  # includes ruff
```

### Run locally
```bash
PUTIO_OAUTH_TOKEN=... TORRENT_PATH=... PUTIO_PATH=... uv run python src/sonarr_putio_helper.py
```

### Lint and format
```bash
uv run ruff check src/sonarr_putio_helper.py
uv run ruff format src/sonarr_putio_helper.py
```

## Development Guidelines

- All changes must be made on feature branches — never commit directly to `master`.
- All new functionality must have corresponding unit tests.
- Merging to `master` requires a Pull Request; direct pushes to `master` are not allowed.
