PYVERSION ?= 3.11.7
PIPVERSION ?= 2023.11.15

PIPENV = pipenv


.PHONY: shell
shell:
	pipenv shell

.PHONY: pre-commit-install
pre-commit-install:
	pip install pre-commit


.PHONY: lint-check
lint-check:
	ruff check src

.PHONY: format-check
format-check:
	ruff format --check src

.PHONY: lint-fix
lint-fix:
	ruff --fix src && ruff format src
