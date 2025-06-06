"""
As BaseRepository is a generic repository, it will be tested using the Question
class for simplicity, but all these tests are applicable to the other models in
the project.
"""

import pytest

from core.models import Question
from core.repositories.base import BaseRepository


class TestCreate:

    def test_create(self, session):
        # Given
        repo = BaseRepository(Question)

        # When
        question = repo.create(question="Question ?")

        # Then
        assert question.question == "Question ?"


class TestUpdate:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, session):
        self.repo = BaseRepository(Question)

        question1 = Question(id=1, question="What is the capital of France?")
        session.add(question1)
        session.commit()

    def test_update(self, session):
        # When
        updated_question = self.repo.update(1, question="What is the capital of Spain?")

        # Then
        assert updated_question.question == "What is the capital of Spain?"

    def test_update_not_found(self, session):
        # When
        updated_question = self.repo.update(2, question="What is the capital of Spain?")

        # Then
        assert not updated_question


class TestGetById:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, session):
        self.repo = BaseRepository(Question)

        question1 = Question(id=1, question="What is the capital of France?")
        session.add(question1)
        session.commit()

    def test_get_by_id(self, session):
        # When
        question = self.repo.get_by_id(1)

        # Then
        assert question.question == "What is the capital of France?"


class TestGetAll:

    def test_get_all(self, session):
        # Given
        self.repo = BaseRepository(Question)

        question1 = Question(id=1, question="What is the capital of France?")
        question2 = Question(id=2, question="What is the capital of Germany?")
        session.add(question1)
        session.add(question2)
        session.commit()

        # When
        questions = self.repo.get_all()

        # Then
        assert questions == [question1, question2]


class TestGetInstanceByKey:

    def test_get_instance_by_key(self, session):
        # Given
        self.repo = BaseRepository(Question)

        question = Question(id=1, question="What is the capital of France?")
        session.add(question)
        session.commit()

        # When
        instance = self.repo.get_instance_by_key(question="What is the capital of France?")

        # Then
        assert instance == question


class TestGetIListByKey:

    def test_get_instance_by_key(self, session):
        # Given
        self.repo = BaseRepository(Question)

        question = Question(id=1, question="What is the capital of France?")
        session.add(question)
        session.commit()

        # When
        instances = self.repo.get_list_by_key(question="What is the capital of France?")

        # Then
        assert instances == [question]

    def test_get_instance_by_key_order_by(self, session):
        # Given
        self.repo = BaseRepository(Question)

        question = Question(id=1, question="What is the capital of France?")
        session.add(question)
        session.commit()
        question2 = Question(id=2, question="What is the capital of Germany?")
        session.add(question2)
        session.commit()

        # When
        instances = self.repo.get_list_by_key(
            order_by=Question.id,
            order="desc"
        )

        # Then
        assert instances[0].id == question2.id

    def test_get_instance_by_key_limit(self, session):
        # Given
        self.repo = BaseRepository(Question)

        question = Question(id=1, question="What is the capital of France?")
        session.add(question)
        session.commit()
        question2 = Question(id=2, question="What is the capital of Germany?")
        session.add(question2)
        session.commit()

        # When
        instances = self.repo.get_list_by_key(limit=1)

        # Then
        assert len(instances) == 1
