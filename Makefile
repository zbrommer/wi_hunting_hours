# Local development. Needs Python plus: pip install pypdf zipcodes
#   make          build, then serve at http://localhost:8000 (Ctrl+C to stop)
#   make build    rebuild dist/ from src/ and data/
#   make serve    same as `make`
#   make icons    redraw src/icons/ (only if the icon design changes)
#   make PORT=9000 serve   use another port
# Recipes are single commands so they work from PowerShell, cmd or Git Bash.

PYTHON ?= python
PORT ?= 8000
YEAR ?= 2026

.PHONY: serve build icons help
.DEFAULT_GOAL := serve

serve: build
	@echo Serving http://localhost:$(PORT) - press Ctrl+C to stop
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 -d dist

build:
	$(PYTHON) build.py --year $(YEAR)

icons:
	$(PYTHON) tools/make_icons.py

help:
	@echo make / make serve   build and serve at http://localhost:$(PORT)
	@echo make build          rebuild dist/
	@echo make icons          redraw src/icons/
