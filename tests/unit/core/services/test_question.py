from unittest.mock import MagicMock

import pytest

from core.models import Question
from core.repositories.question import QuestionRepository
from core.services.question import QuestionService


class TestGetRandomQuestion:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.mock_repo = MagicMock(spec=QuestionRepository)

        self.service = QuestionService()
        self.service.repository = self.mock_repo

    def test_get_random_questions(self):
        # Given
        question1 = Question(id=1, question="What is the capital of France?")
        question2 = Question(id=2, question="What is the capital of Germany?")
        self.mock_repo.get_random_questions.return_value = [question1, question2]

        # When
        result = self.service.get_random_questions(2)

        # Then
        self.mock_repo.get_random_questions.assert_called_once_with(2)
        assert result == [question1.to_dict(), question2.to_dict()]
