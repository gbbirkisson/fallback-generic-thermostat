POETRY:=poetry

.venv: poetry.toml
	$(POETRY) install
	touch .venv

.PHONY: lint-ruff
lint-ruff: .venv
	$(POETRY) run ruff check .

.PHONY: lint-mypy
lint-mypy: .venv
	$(POETRY) run mypy .

.PHONY: lint
lint: lint-ruff lint-mypy

.PHONY: test
test: .venv
	$(POETRY) run pytest

.PHONY: dev
dev: lint test
