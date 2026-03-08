test:
	uv run pytest -xvs
	uv run python integration_tests/custom_workflow/test.py

check:
	uv run ruff format src/ tests/ integration_tests/
	uv run ruff check src/ tests/ integration_tests/
	uv run ruff format --check src/ tests/ integration_tests/

.PHONY: test check
