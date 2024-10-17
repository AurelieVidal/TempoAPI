import pytest
from unittest.mock import patch
from controllers.security_controller import (
    get_questions,
    get_question_by_id,
    get_question_by_question,
    get_random_list,
    post_question,
    delete_question,
    resend_email,
    conforming_response_header
)


@pytest.mark.usefixtures("session")
class TestGetQuestions:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_all_questions = patch(
            "controllers.security_controller.all_questions"
        )
        self.mock_all_questions = self.patch_all_questions.start()
        request.addfinalizer(self.patch_all_questions.stop)

    def test_get_questions(self):
        # Given
        question_list = ["Question 1", "Question 2", "Question 3"]
        self.mock_all_questions.return_value = question_list

        # When
        response, status_code = get_questions()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == question_list
        self.mock_all_questions.assert_called_with()

    def test_get_questions_empty_output(self):
        # Given
        self.mock_all_questions.return_value = None

        # When
        response, status_code = get_questions()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == []
        self.mock_all_questions.assert_called_with()


@pytest.mark.usefixtures("session")
class TestGetQuestionById:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_question_by_id = patch(
            "controllers.security_controller.get_by_id"
        )
        self.mock_question_by_id = self.patch_question_by_id.start()
        request.addfinalizer(self.patch_question_by_id.stop)

    def test_get_question_by_id(self):
        # Given
        id = 1
        kwargs = {"questionId": id}
        question = {"id": 1, "question": "question ?"}
        self.mock_question_by_id.return_value = question

        # When
        response, status_code = get_question_by_id(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "question" in response
        assert response["question"] == question
        self.mock_question_by_id.assert_called_with(id)

    def test_get_question_by_id_no_kwargs(self):
        # When
        response, status_code = get_question_by_id()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_question_by_id.assert_not_called()

    def test_get_question_by_id_invalid_kwargs(self):
        # Given
        kwargs = {"questionId": "id"}
        # When
        response, status_code = get_question_by_id(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_question_by_id.assert_not_called()

    def test_get_question_by_id_not_found(self):
        # Given
        id = 1
        kwargs = {"questionId": id}
        self.mock_question_by_id.return_value = None

        # When
        response, status_code = get_question_by_id(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_question_by_id.assert_called_with(id)


@pytest.mark.usefixtures("session")
class TestGetQuestionByQuestion:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_question_by_question = patch(
            "controllers.security_controller.get_by_question"
        )
        self.mock_question_by_question = (
            self.patch_question_by_question.start()
        )
        request.addfinalizer(self.patch_question_by_question.stop)

    def test_get_question_by_question(self):
        # Given
        question_str = "question ?"
        kwargs = {"question": question_str}
        question = {"id": 1, "question": question_str}
        self.mock_question_by_question.return_value = question

        # When
        response, status_code = get_question_by_question(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "question" in response
        assert response["question"] == question
        self.mock_question_by_question.assert_called_with(question_str)

    def test_get_question_by_question_no_kwargs(self):
        # When
        response, status_code = get_question_by_question()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_question_by_question.assert_not_called()

    def test_get_question_by_question_not_found(self):
        # Given
        question_str = "question ?"
        kwargs = {"question": question_str}
        self.mock_question_by_question.return_value = None

        # When
        response, status_code = get_question_by_question(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_question_by_question.assert_called_with(question_str)


@pytest.mark.usefixtures("session")
class TestRandomList:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_all_questions = patch(
            "controllers.security_controller.all_questions"
        )
        self.mock_all_questions = self.patch_all_questions.start()
        request.addfinalizer(self.patch_all_questions.stop)

        self.patch_get_random_questions = patch(
            "controllers.security_controller.get_random_questions"
        )
        self.mock_get_random_questions = (
            self.patch_get_random_questions.start()
        )
        request.addfinalizer(self.patch_get_random_questions.stop)

    def test_get_random_list(self):
        # Given
        number = 3
        kwargs = {"number": number}
        question_list = [
            "Question 1",
            "Question 2",
            "Question 3",
            "Question 4",
            "Question 5"
        ]
        random_list = ["Question 4", "Question 2", "Question 3"]
        self.mock_all_questions.return_value = question_list
        self.mock_get_random_questions.return_value = random_list

        # When
        response, status_code = get_random_list(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == random_list
        self.mock_all_questions.assert_called_with()
        self.mock_get_random_questions.assert_called_with(number)

    def test_get_random_list_no_kwargs(self):
        # When
        response, status_code = get_random_list()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_random_questions.assert_not_called()
        self.mock_all_questions.assert_not_called()

    def test_get_random_high_number(self):
        # Given
        number = 3
        kwargs = {"number": number}
        question_list = ["Question 1"]
        self.mock_all_questions.return_value = question_list

        # When
        response, status_code = get_random_list(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_random_questions.assert_not_called()
        self.mock_all_questions.assert_called_with()


@pytest.mark.usefixtures("session")
class TestPostQuestion:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_question = patch(
            "controllers.security_controller.get_by_question"
        )
        self.mock_get_by_question = self.patch_get_by_question.start()
        request.addfinalizer(self.patch_get_by_question.stop)

        self.patch_create = patch("controllers.security_controller.create")
        self.mock_create = self.patch_create.start()
        request.addfinalizer(self.patch_create.stop)

    def test_post_question(self):
        # Given
        question_list = [
            "Question 1 ?",
            "Question 2 ?",
            "Question 3 ?",
            "Question 4 ?",
            "Question 5 ?"
        ]
        kwargs = {"body": {
            "questions": question_list
        }}
        self.mock_get_by_question.return_value = None
        self.mock_create.return_value = "question"

        # When
        response, status_code = post_question(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "questions" in response
        assert response["questions"] == [
            "question",
            "question",
            "question",
            "question",
            "question"
        ]
        self.mock_get_by_question.assert_called()
        self.mock_create.assert_called()

    def test_post_question_no_kwargs(self):
        # When
        response, status_code = post_question()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_create.assert_not_called()
        self.mock_get_by_question.assert_not_called()

    def test_post_question_invalid_kwargs(self):
        # Given
        kwargs = {"body": {"fake_item": "fake"}}

        # When
        response, status_code = post_question(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_create.assert_not_called()
        self.mock_get_by_question.assert_not_called()

    def test_post_question_invalid_format(self):
        # Given
        question_list = [
            "Question 1 ?",
            "Question 2",
            "Question 3 ?",
            "Question 4 ?",
            "Question 5 ?"
        ]
        kwargs = {
            "body": {
                "questions": question_list
            }
        }

        # When
        response, status_code = post_question(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_create.assert_not_called()
        self.mock_get_by_question.assert_not_called()

    def test_post_question_already_exist(self):
        # Given
        question_list = [
            "Question 1 ?",
            "Question 2 ?",
            "Question 3 ?",
            "Question 4 ?",
            "Question 5 ?"
        ]
        kwargs = {
            "body": {
                "questions": question_list
            }
        }
        self.mock_get_by_question.return_value = "already exists"
        self.mock_create.return_value = "question"

        # When
        response, status_code = post_question(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_question.assert_called()
        self.mock_create.assert_not_called()


@pytest.mark.usefixtures("session")
class TestDeleteQuestion:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_question_id = patch(
            "controllers.security_controller.get_by_question_id"
        )
        self.mock_get_by_question_id = self.patch_get_by_question_id.start()
        request.addfinalizer(self.patch_get_by_question_id.stop)

        self.patch_get_details = patch(
            "controllers.security_controller.get_details"
        )
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

        self.patch_delete_user_question = patch(
            "controllers.security_controller.delete_user_question"
        )
        self.mock_delete_user_question = (
            self.patch_delete_user_question.start()
        )
        request.addfinalizer(self.patch_delete_user_question.stop)

        self.patch_delete = patch("controllers.security_controller.delete")
        self.mock_delete = self.patch_delete.start()
        request.addfinalizer(self.patch_delete.stop)

    def test_delete_question(self):
        # Given
        question_id = 1
        user_list = ["user1", "user2", "user3"]
        details = {"questions": [1, 2, 3]}
        deleted_question = "deleted question"
        kwargs = {"questionId": question_id}
        self.mock_get_by_question_id.return_value = user_list
        self.mock_get_details.return_value = details
        self.mock_delete.return_value = deleted_question

        # When
        response, status_code = delete_question(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "question" in response
        assert response["question"] == deleted_question
        self.mock_get_by_question_id.assert_called_with(question_id)
        self.mock_get_details.assert_called()
        self.mock_delete_user_question.assert_called_with(question_id)
        self.mock_delete.assert_called_with(question_id)

    def test_delete_question_no_kwargs(self):
        # When
        response, status_code = delete_question()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_question_id.assert_not_called()
        self.mock_get_details.assert_not_called()
        self.mock_delete_user_question.assert_not_called()
        self.mock_delete.assert_not_called()

    def test_delete_question_invalid_kwargs(self):
        # Given
        kwargs = {"questionId": "question_id"}

        # When
        response, status_code = delete_question(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_question_id.assert_not_called()
        self.mock_get_details.assert_not_called()
        self.mock_delete_user_question.assert_not_called()
        self.mock_delete.assert_not_called()

    def test_delete_question_question_still_assigned(self):
        # Given
        question_id = 1
        user_list = ["user1", "user2", "user3"]
        details = {"questions": [1]}
        deleted_question = "deleted question"
        kwargs = {"questionId": question_id}
        self.mock_get_by_question_id.return_value = user_list
        self.mock_get_details.return_value = details
        self.mock_delete.return_value = deleted_question

        # When
        response, status_code = delete_question(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_question_id.assert_called_with(question_id)
        self.mock_get_details.assert_called()
        self.mock_delete_user_question.assert_not_called()
        self.mock_delete.assert_not_called()

    def test_delete_question_question_not_found(self):
        # Given
        question_id = 1
        user_list = ["user1", "user2", "user3"]
        details = {"questions": [1, 2, 3]}
        kwargs = {"questionId": question_id}
        self.mock_get_by_question_id.return_value = user_list
        self.mock_get_details.return_value = details
        self.mock_delete.return_value = None

        # When
        response, status_code = delete_question(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_question_id.assert_called_with(question_id)
        self.mock_get_details.assert_called()
        self.mock_delete_user_question.assert_called_with(question_id)
        self.mock_delete.assert_called_with(question_id)


@pytest.mark.usefixtures("session")
class TestResendEmail:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_username = patch(
            "controllers.security_controller.get_by_username"
        )
        self.mock_get_by_username = self.patch_get_by_username.start()
        request.addfinalizer(self.patch_get_by_username.stop)

        self.patch_get_details = patch(
            "controllers.security_controller.get_details"
        )
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

        self.patch_handle_email = patch(
            "controllers.security_controller.handle_email"
        )
        self.mock_handle_email = self.patch_handle_email.start()
        request.addfinalizer(self.patch_handle_email.stop)

        self.patch_render_template = patch(
            "controllers.security_controller.render_template"
        )
        self.mock_render_template = self.patch_render_template.start()
        request.addfinalizer(self.patch_render_template.stop)

        self.patch_conforming_response_header = patch(
            "controllers.security_controller.conforming_response_header"
        )
        self.mock_conforming_response_header = (
            self.patch_conforming_response_header.start()
        )
        request.addfinalizer(self.patch_conforming_response_header.stop)

    def test_resend_email_success_html(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        user_data = {"email": "user@example.com", "id": 1}
        detailed_user_data = {
            "email": "user@example.com",
            "id": 1,
            "username": "valid_user",
            "phone": "0102030405"
        }
        self.mock_get_by_username.return_value = user_data
        self.mock_get_details.return_value = detailed_user_data

        with test_app.test_request_context(headers={"Accept": "text/html"}):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token="token")
            ) as mock_session:
                # When
                response, status_code, headers = resend_email(**kwargs)

                # Then
                assert status_code == 202
                self.mock_get_by_username.assert_called_with("valid_user")
                self.mock_get_details.assert_called_with(1)
                self.mock_render_template.assert_called_with(
                    'email_resend_template.html'
                )
                self.mock_conforming_response_header.assert_called()
                assert 'email_token' not in mock_session

    def test_resend_email_success_swagger(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        user_data = {"email": "user@example.com", "id": 1}
        detailed_user_data = {
            "email": "user@example.com",
            "id": 1,
            "username": "valid_user",
            "phone": "0102030405"
        }
        self.mock_get_by_username.return_value = user_data
        self.mock_get_details.return_value = detailed_user_data

        with test_app.test_request_context(
                headers={"Accept": "application/json"}
        ):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token="token")
            ) as mock_session:
                # When
                response, status_code, headers = resend_email(**kwargs)

                # Then
                assert status_code == 202
                assert isinstance(response, dict)
                self.mock_get_by_username.assert_called_with("valid_user")
                self.mock_get_details.assert_called_with(1)
                self.mock_render_template.assert_not_called()
                self.mock_conforming_response_header.assert_called()
                assert 'email_token' not in mock_session

    def test_resend_email_no_kwargs(self, test_app):
        with test_app.test_request_context(
                headers={"Accept": "application/json"}
        ):
            with patch("controllers.security_controller.session"):
                # When
                response, status_code = resend_email()

                # Then
                assert status_code == 400
                assert isinstance(response, dict)
                assert "message" in response
                self.mock_render_template.assert_not_called()
                self.mock_conforming_response_header.assert_not_called()
                self.mock_get_by_username.assert_not_called()
                self.mock_get_details.assert_not_called()

    def test_resend_email_user_not_found(self, test_app):
        # Given
        username = "valid_user"
        kwargs = {"username": username}
        self.mock_get_by_username.return_value = None

        with test_app.test_request_context(
                headers={"Accept": "application/json"}
        ):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token="token")
            ):
                # When
                response, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 404
                assert isinstance(response, dict)
                assert "message" in response
                self.mock_render_template.assert_not_called()
                self.mock_conforming_response_header.assert_not_called()
                self.mock_get_by_username.assert_called_with(username)
                self.mock_get_details.assert_not_called()

    def test_resend_email_html_no_token(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        user_data = {"email": "user@example.com", "id": 1}
        detailed_user_data = {
            "email": "user@example.com",
            "id": 1,
            "username": "valid_user",
            "phone": "0102030405"
        }
        self.mock_get_by_username.return_value = user_data
        self.mock_get_details.return_value = detailed_user_data

        with test_app.test_request_context(headers={"Accept": "text/html"}):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token=None)
            ):
                # When
                response, status_code, headers = resend_email(**kwargs)

                # Then
                assert status_code == 202
                self.mock_get_by_username.assert_called_with("valid_user")
                self.mock_get_details.assert_called_with(1)
                self.mock_render_template.assert_called_with(
                    'email_resend_template.html'
                )
                self.mock_conforming_response_header.assert_called()

    def test_resend_email_swagger_no_template(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        user_data = {"email": "user@example.com", "id": 1}
        detailed_user_data = {
            "email": "user@example.com",
            "id": 1,
            "username": "valid_user",
            "phone": "0102030405"
        }
        self.mock_get_by_username.return_value = user_data
        self.mock_get_details.return_value = detailed_user_data

        with test_app.test_request_context(
                headers={"Accept": "application/json"}
        ):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token=None)
            ):
                # When
                response, status_code, headers = resend_email(**kwargs)

                # Then
                assert status_code == 202
                assert isinstance(response, dict)
                self.mock_get_by_username.assert_called_with("valid_user")
                self.mock_get_details.assert_called_with(1)
                self.mock_render_template.assert_not_called()
                self.mock_conforming_response_header.assert_called()

    def test_resend_email_exception_handle_email(self, test_app):
        # Given
        kwargs = {"username": "valid_user"}
        user_data = {"email": "user@example.com", "id": 1}
        detailed_user_data = {
            "email": "user@example.com",
            "id": 1,
            "username": "valid_user",
            "phone": "0102030405"
        }
        self.mock_get_by_username.return_value = user_data
        self.mock_get_details.return_value = detailed_user_data

        with test_app.test_request_context(headers={"Accept": "text/html"}):
            with patch(
                    "controllers.security_controller.session",
                    dict(email_token="token")
            ) as mock_session:
                self.mock_handle_email.side_effect = Exception(
                    "Test exception"
                )

                # When
                response, status_code = resend_email(**kwargs)

                # Then
                assert status_code == 500
                self.mock_get_by_username.assert_called_with("valid_user")
                self.mock_get_details.assert_called_with(1)
                assert response["message"] == (
                    "An error occurred while sending the email"
                )
                self.mock_handle_email.assert_called()
                assert 'email_token' not in mock_session


@pytest.mark.usefixtures("session")
class TestConformingResponseHeader:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_accept_mimetypes = patch(
            "flask.Request.accept_mimetypes",
            autospec=True
        )
        self.mock_accept_mimetypes = self.patch_accept_mimetypes.start()
        request.addfinalizer(self.patch_accept_mimetypes.stop)

    def test_conforming_response_header_html(self, test_app):
        # Given
        self.mock_accept_mimetypes.accept_html = True

        with test_app.test_request_context(headers={"Accept": "text/html"}):
            # When
            response_header = conforming_response_header()

            # Then
            assert response_header == {'Content-Type': 'text/html'}

    def test_conforming_response_header_json(self, test_app):
        # Given
        self.mock_accept_mimetypes.accept_html = False

        with test_app.test_request_context(
                headers={"Accept": "application/json"}
        ):
            # When
            response_header = conforming_response_header()

            # Then
            assert response_header == {'Content-Type': 'application/json'}
