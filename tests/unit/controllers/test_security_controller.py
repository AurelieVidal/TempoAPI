import hashlib
import json
import os
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from controllers.security_controller import (check_user, forgotten_password,
                                             get_last_valid_allow_conn,
                                             get_question_by_id, get_questions,
                                             get_random_list,
                                             validate_connection)
from core.models import (Connection, ConnectionStatusEnum, Question,
                         StatusEnum, UserQuestion)


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
        number = len(self.question_list)
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
        number = len(self.question_list) + 1
        kwargs = {"number": number}

        self.mock_core.question.get_all.return_value = self.question_list

        # When
        response, status_code = get_random_list(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        assert response["message"] == "Length ask is above database length"
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


@pytest.mark.usefixtures("session")
class TestValidateConnection:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("controllers.security_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.connection_main = Connection(
            id=3,
            user_id=user.id,
            date=datetime.now(),
            device="iPad",
            ip_address="192.168.1.12",
            output="Login successful",
            status=ConnectionStatusEnum.SUSPICIOUS
        )

        connection4 = Connection(
            id=4,
            user_id=user.id,
            date=datetime(2025, 5, 4, 17, 45),
            device="Windows PC",
            ip_address="10.0.0.1",
            output="Account locked",
            status=ConnectionStatusEnum.VALIDATION_FAILED
        )

        connection5 = Connection(
            id=5,
            user_id=user.id,
            date=datetime(2025, 5, 5, 12, 0),
            device="Android Phone",
            ip_address="172.16.0.2",
            output="Login failed: timeout",
            status=ConnectionStatusEnum.VALIDATED
        )

        self.connection_main.status = ConnectionStatusEnum.VALIDATION_FAILED
        self.connection_failed_list = [
            self.connection_main,
            connection4,
            connection5
        ]

        self.pepper = "pepper"
        os.environ["PEPPER"] = self.pepper

        self.question_text = "What is your favorite color?"
        question = Question(id=1, question=self.question_text)
        self.answer = "blue"

        expected_hash = hashlib.sha256(
            (self.pepper + self.answer + user.salt).encode("utf-8")
        ).hexdigest().upper()
        user_question = UserQuestion(
            user_id=user.id,
            question=question,
            response=expected_hash
        )

        user.questions = [user_question]
        self.user = user

    @freeze_time(datetime.now())
    def test_validate_connection(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.connection_main.date = datetime.now() - timedelta(minutes=5)
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 200
        assert (
            response["message"]
            == "Connection has been validated, you can try to authenticate again."
        )
        self.mock_core.user.get_instance_by_key.assert_called_once_with(
            username=self.user.username
        )
        first_call_args = self.mock_core.connection.get_list_by_key.call_args_list[0]
        assert first_call_args == mock.call(
            order_by=Connection.date,
            limit=1,
            order="desc",
            id=self.connection_main.id,
            status=ConnectionStatusEnum.SUSPICIOUS
        )
        self.mock_core.connection.update.assert_called_with(
            self.connection_main.id,
            status=ConnectionStatusEnum.VALIDATED
        )

    def test_validate_connection_connection_forgot(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.connection_main.status = ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD
        self.mock_core.connection.get_list_by_key.side_effect = [
            [],
            [self.connection_main],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 200
        assert (
            response["message"]
            == "Connection has been validated, you can try to authenticate again."
        )
        first_call_args = self.mock_core.connection.get_list_by_key.call_args_list[1]
        assert first_call_args == mock.call(
            order_by=Connection.date,
            limit=1,
            order="desc",
            id=self.connection_main.id,
            status=ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD
        )
        self.mock_core.connection.update.assert_called_with(
            self.connection_main.id,
            status=ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD
        )

    def test_validate_connection_connection_forgot_invalid_validation_id(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [],
            [],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 404
        assert response["message"] == "validationId is not valid"
        self.mock_core.connection.update.assert_not_called()

    @freeze_time(datetime.now())
    def test_validate_connection_connection_forgot_expired_validation_id(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.connection_main.date = datetime.now() - timedelta(minutes=5, seconds=1)
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 404
        assert response["message"] == "validationId is expired"
        self.mock_core.connection.update.assert_not_called()

    def test_validate_connection_user_not_found(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = None
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 404
        assert response["message"] == f"User {self.user.username} not found"
        self.mock_core.connection.update.assert_not_called()

    def test_validate_connection_user_banned(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.user.status = StatusEnum.BANNED
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 429
        assert response["message"] == f"User {self.user.username} is banned"
        self.mock_core.connection.update.assert_not_called()

    def test_validate_connection_error_user_question(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.user.questions = []
        self.mock_core.user.get_instance_by_key.return_value = self.user
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": self.answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 500
        assert response["message"] == "Unexpected error"
        self.mock_core.connection.update.assert_not_called()

    @freeze_time(datetime.now())
    def test_validate_connection_invalid_answer(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            self.connection_failed_list
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        answer = "invalid"
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 403
        assert response["message"] == "Provided answer does not match"
        last_call_args = self.mock_core.connection.get_list_by_key.call_args_list[2]
        assert last_call_args == mock.call(
            order_by=Connection.date,
            limit=3,
            order="desc",
            user_id=self.user.id
        )
        self.mock_core.connection.create.assert_called_with(
            user_id=self.user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.VALIDATION_FAILED,
        )

    @freeze_time(datetime.now())
    def test_validate_connection_invalid_answer_no_number_last_conn(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            []
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        answer = "invalid"
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 403
        assert response["message"] == "Provided answer does not match"
        last_call_args = self.mock_core.connection.get_list_by_key.call_args_list[2]
        assert last_call_args == mock.call(
            order_by=Connection.date,
            limit=3,
            order="desc",
            user_id=self.user.id
        )
        self.mock_core.connection.create.assert_called_with(
            user_id=self.user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.VALIDATION_FAILED,
        )

    @freeze_time(datetime.now())
    def test_validate_connection_max_errors(self):
        # Given
        self.connection_main.output = json.dumps({"question": self.question_text})
        self.connection_failed_list[2].status = ConnectionStatusEnum.VALIDATION_FAILED
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection_main],
            [],
            self.connection_failed_list
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        answer = "invalid"
        kwargs = {
            "validationId": self.connection_main.id,
            "username": self.user.username,
            "answer": answer
        }

        # When
        response, status_code = validate_connection(**kwargs)

        # Then
        assert status_code == 429
        assert (
            response["message"]
            == f"Reached max number of tries, user {self.user.username} is now banned. "
               "To reactivate the account please contact admin support at t26159970@gmail.com"
        )
        self.mock_core.user.update.assert_called_with(
            self.user.id,
            status=StatusEnum.BANNED
        )
        self.mock_core.connection.create.assert_called_with(
            user_id=self.user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.VALIDATION_FAILED,
        )


@pytest.mark.usefixtures("session")
class TestForgottenPassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("controllers.security_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_email = patch("controllers.security_controller.handle_email_forgotten_password")
        self.mock_email = self.patch_email.start()
        request.addfinalizer(self.patch_email.stop)

        self.user = user

        self.question_text = "Quel est ton café préféré ?"
        question = Question(id=1, question=self.question_text)
        self.answer = "blue"

        self.pepper = "pepper"
        os.environ["PEPPER"] = self.pepper
        expected_hash = hashlib.sha256(
            (self.pepper + self.answer + user.salt).encode("utf-8")
        ).hexdigest().upper()

        user_question = UserQuestion(
            user_id=user.id,
            question=question,
            response=expected_hash
        )
        self. user.questions = [user_question]

        self.last_conn = Connection(
            id=99,
            user_id=user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD
        )

        self.failed_conn = Connection(
            id=100,
            user_id=user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.VALIDATION_FAILED
        )

    @freeze_time(datetime.now())
    @pytest.mark.parametrize(
        "connections_list",
        [
            pytest.param(
                lambda self: [self.last_conn],
                id="single_valid_connection"
            ),
            pytest.param(
                lambda self: [self.failed_conn, self.failed_conn, self.last_conn],
                id="failed_then_valid_connection"
            ),
        ]
    )
    @freeze_time(datetime.now())
    def test_forgotten_password(self, connections_list):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_core.connection.get_list_by_key.return_value = connections_list(self)
        kwargs = {"username": self.user.username}

        # When
        response, status_code = forgotten_password(**kwargs)

        # Then
        assert status_code == 200
        assert response["message"] == "Demand validated, an email has been sent to the user"
        self.mock_core.user.get_instance_by_key.assert_called_once_with(username=self.user.username)
        self.mock_core.connection.get_list_by_key.assert_called_once_with(
            order_by=Connection.date,
            limit=5,
            order="desc",
            user_id=self.user.id
        )
        self.mock_email.assert_called_once_with(self.user)

    @freeze_time(datetime.now())
    def test_forgotten_password_creates_connection(self):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_core.connection.get_list_by_key.return_value = []

        mock_create = self.mock_core.connection.create
        mock_create.return_value.id = 123

        kwargs = {"username": self.user.username}

        # When
        response, status_code = forgotten_password(**kwargs)

        # Then
        assert status_code == 412
        assert (
            response["message"]
            == "You need to validate connection by answering a security question"
        )
        assert response["question"] == self.question_text
        assert response["validation_id"] == 123

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["user_id"] == self.user.id
        assert call_args["date"] == datetime.now()
        assert call_args["status"] == ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD
        output_json = call_args["output"]
        assert isinstance(output_json, str)
        assert "Quel est ton café préféré ?" in output_json
        assert "\\u00e9" not in output_json

    @freeze_time(datetime.now())
    @pytest.mark.parametrize(
        "status",
        [
            ConnectionStatusEnum.SUSPICIOUS,
            ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD,
        ]
    )
    def test_forgotten_password_error_connection_status(self, status):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        last_conn = Connection(
            id=99,
            user_id=self.user.id,
            date=datetime.now() - timedelta(minutes=5),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=status
        )
        self.mock_core.connection.get_list_by_key.return_value = [last_conn]

        mock_create = self.mock_core.connection.create
        mock_create.return_value.id = 123

        kwargs = {"username": self.user.username}

        # When
        response, status_code = forgotten_password(**kwargs)

        # Then
        assert status_code == 412
        assert (
            response["message"]
            == "You need to validate connection by answering a security question"
        )
        assert response["question"] == self.question_text
        assert response["validation_id"] == 123

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["user_id"] == self.user.id
        assert call_args["status"] == ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD
        assert json.loads(call_args["output"])["question"] == self.question_text

    def test_forgotten_password_user_not_found(self):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = None
        kwargs = {"username": "unknown_user"}

        # When
        response, status_code = forgotten_password(**kwargs)

        # Then
        assert status_code == 404
        assert response["message"] == "User unknown_user not found"


class TestGetLastValidAllowConn:
    @pytest.fixture(autouse=True)
    def setup_method(self, user):
        self.user = user

    def test_get_last_valid_conn(self):
        # Given
        last_conn = Connection(
            id=99,
            user_id=self.user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD
        )

        # When
        result = get_last_valid_allow_conn([last_conn])

        # Then
        assert result == last_conn

    def test_get_last_valid_conn_invalid_status(self):
        # Given
        last_conn = Connection(
            id=99,
            user_id=self.user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.SUSPICIOUS
        )

        # When
        result = get_last_valid_allow_conn([last_conn])

        # Then
        assert not result

    def test_get_last_valid_conn_failed_before(self):
        # Given
        last_conn = Connection(
            id=99,
            user_id=self.user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD
        )

        failed_conn = Connection(
            id=99,
            user_id=self.user.id,
            date=datetime.now() - timedelta(minutes=4, seconds=30),
            device="iPhone",
            ip_address="1.2.3.4",
            output="",
            status=ConnectionStatusEnum.VALIDATION_FAILED
        )

        # When
        result = get_last_valid_allow_conn([failed_conn, last_conn])

        # Then
        assert result == last_conn
