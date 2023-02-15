#!/usr/bin/env bash

git init

pip install -U poetry

poetry add --lock \
  fastapi \
  "uvicorn[standard]" \
  "SQLAlchemy[asyncio]" \
  asyncpg \
  httpx \
  "python-jose[cryptography]" \
  click \
  cachetools

poetry add --lock --group dev \
  alembic \
  bandit \
  black \
  flake8 \
  flake8-pyproject \
  isort \
  mypy \
  pytest \
  pytest-cov \
  pytest-mock \
  pytest_postgresql \
  pytest-xdist
