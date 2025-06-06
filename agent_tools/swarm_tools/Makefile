.PHONY: install test lint format clean build

install:
	pip install -e .

test:
	pytest tests/ -v --cov=scanner

lint:
	black --check scanner tests
	isort --check-only scanner tests
	mypy scanner tests

format:
	black scanner tests
	isort scanner tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py sdist bdist_wheel

publish: build
	twine upload dist/* 