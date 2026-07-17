# Agentic Atlas
# Run `make` or `make help` to list targets.

.DEFAULT_GOAL := help

VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF   := $(VENV)/bin/ruff
ATLAS  := $(VENV)/bin/agentic-atlas

# Overridable on the command line, e.g. make profile TARGET=/path ANSWERS=answers.json
RUBRIC  ?= rubric/v1
TARGET  ?=
ANSWERS ?=
FORMAT  ?= text

.PHONY: help setup install test check lint fmt format validate docs docs-check profile clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# Rebuild the environment whenever pyproject.toml changes.
$(VENV): pyproject.toml
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -e ".[dev]"
	@touch $(VENV)
	@echo "environment ready. try: make test"

setup: $(VENV) ## Create the venv and install the package (editable) with dev deps

install: setup ## Alias for setup

test: setup ## Run the test suite
	$(PYTEST) -q

lint: setup ## Lint with ruff
	$(RUFF) check .

fmt: setup ## Format the code with ruff
	$(RUFF) format .

format: fmt ## Alias for fmt

check: lint docs-check test ## Lint, check docs sync, then test (the CI gate)

validate: setup ## Validate the rubric against the schema (RUBRIC=...)
	$(ATLAS) validate $(RUBRIC)

docs: setup ## Regenerate axis README scoring blocks from axis.yaml
	$(ATLAS) docs $(RUBRIC)

docs-check: setup ## Fail if any axis README scoring block is stale
	$(ATLAS) docs $(RUBRIC) --check

profile: setup ## Profile a target: make profile TARGET=/path [ANSWERS=answers.json FORMAT=md]
	@test -n "$(TARGET)" || { \
		echo "usage: make profile TARGET=/path/to/approach [ANSWERS=answers.json FORMAT=text|md|json]"; \
		exit 2; }
	$(ATLAS) profile "$(TARGET)" --rubric "$(RUBRIC)" $(if $(ANSWERS),--answers "$(ANSWERS)",) --format "$(FORMAT)"

clean: ## Remove the venv, caches, and build artifacts
	rm -rf $(VENV) .pytest_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
