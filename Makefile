PYTHON = python
TEST_DIR = tests  # Remplace par le chemin vers ton dossier de tests si nécessaire
FLAKE8 = flake8

# Cible par défaut
all: test

# Cible pour exécuter les tests avec couverture
test:
	DATABASE=sqlite:///:memory: \
	MAIL_USERNAME=fake@example.com \
	MAIL_PASSWORD=fakepassword \
	SESSION_SECRET_KEY=fakesecretkey \
	$(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=100 --cov-config=.coveragerc $(TEST_DIR)

# Cible pour vérifier la qualité du code avec Flake8
flake:
	$(FLAKE8) --exclude=venv .

# Cible pour exécuter les tests avec Flake8
test-flake:
	$(FLAKE8) --exclude=venv . && DATABASE=sqlite:///:memory: $(PYTHON) -m pytest --cov=. --cov-report=term-missing --cov-fail-under=100 --cov-config=.coveragerc $(TEST_DIR)


# Cible pour vérifier l'ordre des imports avec isort
isort-check:
	isort --check . --skip venv

# Cible pour corriger l'ordre des imports avec isort
isort:
	isort . --skip venv

# Cible pour vérifier les types avec Mypy
mypy:
	mypy --exclude venv .

# Cible pour vérifier la sécurité du code avec Bandit
bandit:
	bandit -r . --exclude venv

# Cible pour vérifier les vulnérabilités des dépendances avec Safety
safety:
	safety check -r requirements.txt

# Cible pour nettoyer les fichiers pyc
clean:
	find . -name "*.pyc" -exec rm -f {} \;

# Cible pour lancer l'API en mode développement
run_dev:
	uvicorn app:app --reload

# Cible pour lancer l'API en production
run:
	gunicorn -k uvicorn.workers.UvicornWorker app:app

# Cible pour installer les dépendances
install:
	pip install -r requirements.txt

# Cible pour afficher l'aide
help:
	@echo "Makefile Commands:"
	@echo "  make install      - Install all necessary dependencies"
	@echo "  make run_dev      - Launch the API in a development environment"
	@echo "  make run          - Launch the API like production"
	@echo "  make test         - Run the tests with coverage"
	@echo "  make flake        - Run Flake8 for code quality"
	@echo "  make test-flake   - Run both tests and Flake8"
	@echo "  make isort        - Auto-fix import order with isort"
	@echo "  make isort-check  - Check import order with isort"
	@echo "  make mypy         - Check types using Mypy"
	@echo "  make bandit       - Run Bandit for security checks"
	@echo "  make safety       - Check for vulnerable dependencies with Safety"
	@echo "  make clean        - Remove Python bytecode files"
	@echo "  make help         - Show this help message"