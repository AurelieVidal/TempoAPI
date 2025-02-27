"""
As BaseService is a generic repository, it will be tested using the Question
class for simplicity, but all these tests are applicable to the other models in
the project.
"""

from core.models import Question
from core.repositories.base import BaseRepository

from core.services.base import BaseService


class TestCreate:

    def test_create(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)

        # When
        question = service.create(question="What is the capital of France?")

        # Then
        assert question is not None
        assert question.question == "What is the capital of France?"


class TestUpdate:

    def test_update(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)
        question = service.create(question="Original question")

        # When
        updated_question = service.update(question.id, question="Updated question")

        # Then
        assert updated_question is not None
        assert updated_question.question == "Updated question"


class TestGetById:

    def test_get_by_id(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)
        question = service.create(question="What is the capital of France?")

        # When
        retrieved_question = service.get_by_id(question.id)

        # Then
        assert retrieved_question is not None
        assert retrieved_question.id == question.id
        assert retrieved_question.question == "What is the capital of France?"


class TestGetAll:

    def test_get_all(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)
        question1 = service.create(question="What is the capital of France?")
        question2 = service.create(question="What is the capital of Germany?")

        # When
        questions = service.get_all()

        # Then
        assert len(questions) == 2
        assert question1 in questions
        assert question2 in questions


class TestGetInstanceByKey:

    def test_get_instance_by_key(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)
        question = service.create(question="What is the capital of France?")

        # When
        retrieved_question = service.get_instance_by_key(question=question.question)

        # Then
        assert retrieved_question is not None
        assert retrieved_question.id == question.id


class TestGetIListByKey:

    def test_get_list_by_key(self, session):
        # Given
        repo = BaseRepository(Question)
        service = BaseService(repo)
        question = service.create(question="What is the capital of France?")

        # When
        questions = service.get_list_by_key(question="What is the capital of France?")

        # Then
        assert len(questions) == 1
        assert questions == [question]
