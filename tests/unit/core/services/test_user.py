import json
from unittest.mock import MagicMock

import pytest

from core.repositories.user import UserRepository
from core.services.user import UserService


class TestGetDetails:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_repo = MagicMock(spec=UserRepository)

        self.service = UserService()
        self.service.repository = self.mock_repo

    def test_get_details(self):
        # Given
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "test_user"
        mock_user.email = "test@example.com"
        mock_user.devices = json.dumps(["device1", "device2"])
        mock_user.status.value = "active"
        mock_user.phone = "+123456789"
        mock_user.question = "What is the capital of France?"
        mock_user.question_id = 1

        mock_user2 = mock_user.deepcopy()
        mock_user2.question = "What is the capital of Germany?"
        mock_user2.question_id = 2

        self.mock_repo.get_details.return_value = [mock_user, mock_user2]

        # When
        result = self.service.get_details(1)

        # Then
        self.mock_repo.get_details.assert_called_once_with(1)
        assert result == {
            "id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "questions": [
                {"question": "What is the capital of France?", "id": 1},
                {"question": "What is the capital of Germany?", "id": 2},
            ],
            "devices": ["device1", "device2"],
            "status": "active",
            "phone": "+123456789",
        }

    def test_get_details_not_found(self):
        # Given
        self.mock_repo.get_details.return_value = []

        # When
        result = self.service.get_details(2)

        # Then
        self.mock_repo.get_details.assert_called_once_with(2)
        assert result is None
