PYTHON = python
TEST_DIR = tests
FLAKE8 = flake8
PYLINT = pylint

all: test

test:
	DATABASE=sqlite:///:memory: \
	MAIL_USERNAME=fake@example.com \
	MAIL_PASSWORD=fakepassword \
	SESSION_SECRET_KEY=fakesecretkey \
	TWILIO_ACCOUNT_SID=account \
	TWILIO_AUTH_TOKEN=token \
	TWILIO_SERVICE=service \
	$(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=100 --cov-config=.coveragerc $(TEST_DIR)

mutmut:
	mutmut run

mutmut_results:
	mutmut results

flake:
	$(FLAKE8) --exclude=venv,mutants .

isort-check:
	isort --check . --skip venv --skip mutants

isort:
	isort . --skip venv --skip mutants

pylint:
	$(PYLINT) --rcfile=.pylintrc --disable=R1710,R0401 --fail-under=9.75 $(shell find . -name "*.py" ! -path "./venv/*" ! -path "./mutants/*" ! -path "./alembic/versions/*" ! -path "./tests/*")

run_dev:
	uvicorn app:app --reload --reload-exclude "venv/*"

run:
	gunicorn -k uvicorn.workers.UvicornWorker app:app

install:
	pip install -r requirements.txt

help:
	@echo "Makefile Commands:"
	@echo "  make install      - Install all necessary dependencies"
	@echo "  make run_dev      - Launch the API in a development environment"
	@echo "  make run          - Launch the API like production"
	@echo "  make test         - Run the tests with coverage"
	@echo "  make flake        - Run Flake8 for code quality"
	@echo "  make isort        - Auto-fix import order with isort"
	@echo "  make isort-check  - Check import order with isort"
	@echo "  make pylint       - Run Pylint for static analysis"
	@echo "  make help         - Show this help message"
	@echo "  make mutmut       - Run mutation testing with mutmut"