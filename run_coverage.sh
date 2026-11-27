#!/usr/bin/env bash
set -euo pipefail
pytest \
  --cov=src --cov-config=.coveragerc --cov-report=term-missing "$@"
