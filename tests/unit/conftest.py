import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

from app import app
from core.models.user import StatusEnum, User
from extensions import db


@pytest.fixture(scope="module")
def test_app():
    """
    Fixture to initialize testing application
    """
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.app.config["TESTING"] = True
    app.app.config["TWILIO_ACCOUNT_SID"] = "account_id"
    app.app.config["TWILIO_AUTH_TOKEN"] = "token"
    app.app.config["TWILIO_SERVICE"] = "service"

    with app.app.app_context():
        db.create_all()
        yield app.app

        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
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
    return test_app.test_client()


@pytest.fixture
def user():
    return User(
        id=1,
        username="username",
        email="username@email.com",
        password="password",
        salt="abcde",
        phone="0102030405",
        devices="['iphone']",
        status=StatusEnum.READY
    )
