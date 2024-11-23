# Makefile for building and publishing the Python package

.PHONY: clean build publish publish-test install test

# Remove build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist *.egg-info

# Build the package
build: clean
	@echo "Building the package..."
	python -m build

# Upload to TestPyPI
publish-test: build
	@echo "Uploading to TestPyPI..."
	python -m twine upload --repository testpypi dist/*

# Upload to PyPI
publish: build
	@echo "Uploading to PyPI..."
	python -m twine upload dist/*

# Install the package locally
install:
	@echo "Installing the package locally..."
	pip install .

# Run tests
test:
	@echo "Running tests..."
	python -m unittest discover tests

# Format code using Black
format:
	@echo "Formatting code with Black..."
	black src/ tests/

# Lint code using Flake8
lint:
	@echo "Linting code with Flake8..."
	flake8 src/ tests/
