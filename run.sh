#!/usr/bin/env bash
# Local dev helper:  ./run.sh [setup|api|worker|review|test]
set -euo pipefail

case "${1:-api}" in
  setup)
    python -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -r requirements.txt
    [ -f .env ] || cp .env.example .env
    python -m app.main init-db
    ;;
  api)    python -m app.main serve ;;
  worker) celery -A app.pipeline.batch_processor.celery_app worker --loglevel=info ;;
  review) streamlit run app/review_queue/review_ui.py ;;
  test)   pytest -v ;;
  *) echo "Usage: ./run.sh [setup|api|worker|review|test]"; exit 1 ;;
esac;