# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sonarr Putio Helper is a Python application that monitors a local directory for `.torrent`/`.magnet` files and uploads them to Put.io for download. It runs as a Docker container with configurable user/group IDs for proper file permissions.

## Architecture

Single-file Python app (`src/sonarr-putio-helper.py`) with a linear startup flow:
1. Collect environment variables (`collect_environment`)
2. Verify local filesystem paths (`verify_filesystem`)
3. Authenticate with Put.io API (`connect_putio`)
4. Resolve/create target folder on Put.io (`get_or_create_putio_folder`)
5. Start a watchdog `Observer` that triggers Put.io transfers on file creation events
6. Run polling loop until interrupted

Uses Go-style `(result, error)` tuple returns throughout.

Key dependencies: `putiopy` (Put.io API client), `watchdog` (filesystem event monitoring).

## Required Environment Variables

- `PUTIO_OAUTH_TOKEN` - Put.io OAuth token
- `TORRENT_PATH` - Local path to watch for torrent/magnet files
- `PUTIO_PATH` - Target folder path on Put.io
- `TORRENT_POLL_DELAY` - Poll interval in seconds (default: 1)
- `PUID`/`PGID` - Container user/group IDs (default: 1337/1338)

## Commands

### Build Docker image
```bash
cd src && docker build -t putio-helper .
```

### Install dependencies locally
```bash
pip install -r src/requirements.txt
pip install -r src/requirements-dev.txt  # adds flake8, black
```

### Run locally
```bash
PUTIO_OAUTH_TOKEN=... TORRENT_PATH=... PUTIO_PATH=... python src/sonarr-putio-helper.py
```

### Lint and format
```bash
flake8 src/sonarr-putio-helper.py
black src/sonarr-putio-helper.py
```

## Development Guidelines

- All changes must be made on feature branches — never commit directly to `master`.
- All new functionality must have corresponding unit tests.
- Merging to `master` requires a Pull Request; direct pushes to `master` are not allowed.
