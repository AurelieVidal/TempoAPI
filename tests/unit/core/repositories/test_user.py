import pytest

from core.models import Question, UserQuestion
from core.repositories.user import UserRepository


class TestGetDetails:

    @pytest.fixture(autouse=True)
    def setup_method(self, session, user):
        self.repo = UserRepository()

        session.add(user)
        session.commit()

        self.questions = [
            Question(id=1, question="What is the capital of France?"),
            Question(id=2, question="What is the capital of Germany?"),
        ]
        session.add_all(self.questions)
        session.commit()

        user_questions = [
            UserQuestion(user_id=user.id, question_id=self.questions[0].id, response="Paris"),
            UserQuestion(
                user_id=user.id,
                question_id=self.questions[1].id,
                response="Berlin"
            ),
        ]
        session.add_all(user_questions)
        session.commit()

    def test_get_details(self, session, user):
        # When
        details = self.repo.get_details(user.id)

        # Then
        assert len(details) == 2

        for result, question in zip(details, self.questions):
            assert result.id == user.id
            assert result.username == user.username
            assert result.email == user.email
            assert result.devices == user.devices
            assert result.status == user.status
            assert result.phone == user.phone
            assert result.question == question.question
            assert result.question_id == question.id
