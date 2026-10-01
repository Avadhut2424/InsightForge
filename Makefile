.PHONY: test help

help:
	@echo "InsightForge AI Makefile commands:"
	@echo "  make test    - Run consolidated automated test suite with full timing"

test:
	python run_suite.py
