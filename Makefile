# Variables
PYTHON = python
TEST_DIR = tests  # Remplace par le chemin vers ton dossier de tests si nécessaire
FLAKE8 = flake8

# Cible par défaut
all: test

# Cible pour exécuter les tests avec couverture
test:
	DATABASE=sqlite:///:memory: $(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=100 --cov-config=.coveragerc $(TEST_DIR)

# Cible pour vérifier la qualité du code avec Flake8
flake:
	$(FLAKE8) --exclude=venv .

# Cible pour exécuter les tests avec Flake8
test-flake:
	$(FLAKE8) --exclude=venv . && DATABASE=sqlite:///:memory: $(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=100 --cov-config=.coveragerc $(TEST_DIR)

# Cible pour nettoyer les fichiers pyc
clean:
	find . -name "*.pyc" -exec rm -f {} \;

run_dev:
	uvicorn app:app --reload

run:
	gunicorn -k uvicorn.workers.UvicornWorker app:app

install:
	pip install -r requirements.txt

# Cible pour afficher l'aide
help:
	@echo "Makefile Commands:"
	@echo "  make install      - Install all necessary dependencies"
	@echo "  make run_dev      - Launch the API uin a development environment"
	@echo "  make run          - Launch the API like production"
	@echo "  make test         - Run the tests with coverage"
	@echo "  make flake        - Run Flake8 for code quality"
	@echo "  make test-flake   - Run both tests and Flake8"
	@echo "  make clean        - Remove Python bytecode files"
	@echo "  make help         - Show this help message"
