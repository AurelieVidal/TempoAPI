import json
import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

from app import app
from core.models import Connection, ConnectionStatusEnum, Token
from core.models.user import StatusEnum, User
from extensions import db


@pytest.fixture(scope="module")
def test_app():
    """
    Fixture to initialize testing application
    """
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.app.config["TESTING"] = True

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
        devices=json.dumps(["iphone"]),
        status=StatusEnum.READY
    )


@pytest.fixture
def connection(user):
    return Connection(
        id=1,
        user_id=user.id,
        date=datetime(2025, 1, 1),
        device="iphone",
        ip_address="0.0.0.0",
        output=json.dumps({"question": "What is the capital of France ?"}),
        status=ConnectionStatusEnum.SUCCESS
    )


@pytest.fixture
def token(user):
    return Token(
        id=1,
        user_id=user.id,
        expiration_date=datetime(2025, 1, 1),
        value=str(uuid.uuid4()),
        is_active=True
    )
