# ========= SEC-COPILOT Makefile (uv version) =========

VENV := .venv

# Ensure venv exists
$(VENV):
	uv venv $(VENV)

# Install dependencies from requirements.txt
install: $(VENV)
	uv pip install --upgrade pip
	uv pip install -r requirements.txt


# Run API server (FastAPI + Uvicorn)
run-api:
	uv run uvicorn app.main:app --reload --port 8000

# Run tests (quiet mode)
test:
	uv run pytest -q

# Lint code with Ruff
lint:
	uv run ruff check .

# Format code with Ruff
fmt:
	uv run ruff format .

# Format code with Black + isort (optional alternative)
format:
	uv run black app/
	uv run isort app/

# Clean environment + caches
clean:
	rm -rf $(VENV) __pycache__ */__pycache__ .pytest_cache

# Open interactive shell inside venv
shell:
	uv run bash

.PHONY: install run-api test lint fmt format clean shell
