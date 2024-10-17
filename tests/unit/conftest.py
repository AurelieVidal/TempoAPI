import pytest
from app import app
from extensions import db
from sqlalchemy.orm import scoped_session, sessionmaker


@pytest.fixture(scope='module')
def test_app():
    """
    Fixture to initialize testing application
    """
    app.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False

    with app.app.app_context():
        db.create_all()
        yield app.app

        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def session(test_app):
    """
    Fixture to handle a database session
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    db.session = session
    yield session

    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def client(test_app):
    return app.test_client()
