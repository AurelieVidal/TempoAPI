import uuid
from datetime import datetime, timedelta

import pytest

from core.models import Token
from core.repositories.token import TokenRepository


class TestTokenRepository:
    @pytest.fixture(autouse=True)
    def setup_method(self, session, user):
        self.repo = TokenRepository()
        self.user = user

        # Création de deux tokens pour le même utilisateur
        self.old_token = Token(
            id=1,
            user_id=user.id,
            expiration_date=datetime.now() + timedelta(days=5),
            value=str(uuid.uuid4()),
            is_active=True
        )
        session.add(self.old_token)
        session.commit()

    def test_create_deactivates_old_tokens(self, session):
        # Given
        new_token_data = {
            "user_id": self.user.id,
            "expiration_date": datetime.now() + timedelta(days=10),
            "value": str(uuid.uuid4()),
            "is_active": True
        }

        # When
        created_token = self.repo.create(**new_token_data)

        # Then
        session.refresh(self.old_token)  # recharger depuis la DB
        assert created_token.user_id == self.user.id
        assert created_token.is_active is True
        assert self.old_token.is_active is False  # l’ancien token doit être désactivé

        # Et on peut vérifier qu’il n’y a qu’un seul token actif pour ce user
        active_tokens = session.query(Token).filter_by(user_id=self.user.id, is_active=True).all()
        assert len(active_tokens) == 1
        assert active_tokens[0].id == created_token.id

    def test_create_user_not_found(self, session):
        # Given
        new_token_data = {
            "user_id": None,
            "expiration_date": datetime.now() + timedelta(days=10),
            "value": str(uuid.uuid4()),
            "is_active": True
        }

        # When, Then
        with pytest.raises(ValueError):
            self.repo.create(**new_token_data)
