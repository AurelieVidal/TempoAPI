import pytest

from core.models import Question
from core.repositories.question import QuestionRepository


class TestGetAll:

    @pytest.fixture(autouse=True)
    def setup_method(self, session):
        self.repo = QuestionRepository()

        self.questions = [
            Question(id=1, question="What is the capital of France?"),
            Question(id=2, question="What is the capital of Germany?"),
            Question(id=3, question="What is the capital of Spain?"),
            Question(id=4, question="What is the capital of Italy?"),
        ]
        session.add_all(self.questions)
        session.commit()

    def test_get_random_questions(self, session):
        # When
        random_questions = self.repo.get_random_questions(2)

        # Then
        assert len(random_questions) == 2
        returned_ids = {q.id for q in random_questions}
        valid_ids = {q.id for q in self.questions}
        assert returned_ids.issubset(valid_ids)
