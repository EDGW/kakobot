# Local documentation and plugin archive builds.
PYTHON ?= python3
DOCS_ARGS ?=

.PHONY: help docs publish
.DEFAULT_GOAL := help

help:
	@echo "make docs     Generate CHAT/GROUP JPEG cards in docs/pics/"
	@echo "make publish  Generate documentation, then build the plugin ZIP in dist/"
	@echo "Override PYTHON or DOCS_ARGS as needed. No upload or push is performed."

docs:
	$(PYTHON) -m src.tooling.docs_images $(DOCS_ARGS)

publish: docs
	$(PYTHON) -m src.tooling.package
