run-api:
	uv run uvicorn app.main:app --reload --port 8000

test:
	uv run pytest -q

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
