#!/usr/bin/env bash
set -euo pipefail
pytest -c tests_pyramid/pytest.ini tests_pyramid "$@"
