# Makefile for MD2PDF Pro

.PHONY: help install dev test lint format clean build publish

help:
	@echo "MD2PDF Pro - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Install development dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linters"
	@echo "  format     - Format code"
	@echo "  clean      - Clean build artifacts"
	@echo "  build      - Build package"
	@echo "  publish    - Publish to PyPI"

install:
	pip install -r requirements.txt

dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=xml

lint:
	ruff check src/
	mypy src/

format:
	black src/
	ruff check --fix src/
	isort src/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build

publish:
	python -m twine upload dist/*

doctor:
	python -m md2pdf_pro.cli doctor

.DEFAULT_GOAL := help
