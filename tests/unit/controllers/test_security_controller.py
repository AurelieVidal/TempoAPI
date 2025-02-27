from unittest.mock import patch

import pytest

from controllers.security_controller import (check_user, get_question_by_id,
                                             get_questions, get_random_list)
from core.models import Question


@pytest.mark.usefixtures("session")
class TestGetQuestions:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("controllers.security_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

    def test_get_questions(self):
        # Given
        question1 = Question(id=1, question="Question1 ?")
        question2 = Question(id=2, question="Question2 ?")
        self.mock_core.question.get_all.return_value = [question1, question2]

        # When
        response, status_code = get_questions()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == [question1.to_dict(), question2.to_dict()]
        self.mock_core.question.get_all.assert_called_with()

    def test_get_questions_empty_output(self):
        # Given
        self.mock_core.question.get_all.return_value = []

        # When
        response, status_code = get_questions()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == []
        self.mock_core.question.get_all.assert_called_with()


@pytest.mark.usefixtures("session")
class TestGetQuestionById:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("controllers.security_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

    def test_get_question_by_id(self):
        # Given
        question = Question(id=1, question="Question1 ?")
        kwargs = {"questionId": question.id}
        self.mock_core.question.get_by_id.return_value = question

        # When
        response, status_code = get_question_by_id(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "question" in response
        assert response["question"] == question.to_dict()
        self.mock_core.question.get_by_id.assert_called_with(question.id)

    def test_get_question_by_id_not_found(self):
        # Given
        kwargs = {"questionId": 10}
        self.mock_core.question.get_by_id.return_value = None

        # When
        response, status_code = get_question_by_id(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(10)


@pytest.mark.usefixtures("session")
class TestRandomList:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("controllers.security_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        question1 = Question(id=1, question="Question1 ?")
        self.question2 = Question(id=2, question="Question2 ?")
        self.question3 = Question(id=3, question="Question3 ?")
        self.question4 = Question(id=4, question="Question4 ?")
        question5 = Question(id=5, question="Question5 ?")

        self.question_list = [
            question1,
            self.question2,
            self.question3,
            self.question4,
            question5
        ]

    def test_get_random_list(self):
        # Given
        number = 3
        kwargs = {"number": number}

        random_list = [self.question4.to_dict(), self.question2.to_dict(), self.question3.to_dict()]
        self.mock_core.question.get_all.return_value = self.question_list
        self.mock_core.question.get_random_questions.return_value = random_list

        # When
        response, status_code = get_random_list(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == random_list
        self.mock_core.question.get_all.assert_called_with()
        self.mock_core.question.get_random_questions.assert_called_with(number)

    def test_get_random_list_invalid_number(self):
        # Given
        number = 13
        kwargs = {"number": number}

        self.mock_core.question.get_all.return_value = self.question_list

        # When
        response, status_code = get_random_list(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_all.assert_called_with()
        self.mock_core.question.get_random_questions.assert_not_called()


@pytest.mark.usefixtures("session")
class TestCheckUser:

    def test_check_user(self):
        # When
        response, status_code = check_user()

        # Then
        assert status_code == 200
        assert response == {"message": "User successfully authenticated"}
