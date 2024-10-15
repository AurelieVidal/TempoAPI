import pytest
from app import app  # Importe l'application configurée dans app.py
from extensions import db
from sqlalchemy.orm import scoped_session, sessionmaker

@pytest.fixture(scope='module')
def test_app():
    """
    Fixture qui initialise l'application et un contexte d'application.
    """
    # Configure l'application pour utiliser une base de données SQLite en mémoire
    app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False  # Désactive CSRF pour les tests

    # Pousse un contexte d'application pour chaque test
    with app.app.app_context():
        # Crée les tables pour la base de données de test
        db.create_all()

        yield app.app  # Fournit l'application pour les tests

        # Après les tests, supprime toutes les données et détruit la base
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def session(test_app):
    """
    Fixture pour gérer une session de base de données pour chaque test.
    """
    # Connexion à la base de données temporaire
    connection = db.engine.connect()
    transaction = connection.begin()

    # Utilisation de scoped_session pour gérer la session
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    db.session = session  # Associe la session temporaire au db

    yield session  # Fournit la session pour les tests

    # Après les tests, rollback la transaction et ferme la connexion
    transaction.rollback()
    connection.close()
    session.remove()


from flask.sessions import SecureCookieSessionInterface

@pytest.fixture
def client(test_app):
    return app.test_client()

