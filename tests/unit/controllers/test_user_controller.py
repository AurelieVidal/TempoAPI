import hashlib
import os
import smtplib
from unittest.mock import patch

import pytest

from adapters.hibp_client import HibpClient
from controllers.user_controller import (generate_substrings,
                                         get_user_by_username,
                                         get_user_details, get_user_info,
                                         get_users, post_users)
from core.models import Question
from core.models.role import Role, RoleEnum
from core.models.user import StatusEnum, User
from tests.unit.testing_utils import generate_password


@pytest.mark.usefixtures("session")
class TestGetUsers:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("controllers.user_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.user1 = user

        self.user2 = User(
            id=2,
            username="second",
            email="second@email.com",
            password="password",
            salt="abcde",
            phone="0102030405",
            devices="['iphone']",
            status=StatusEnum.CHECKING_EMAIL
        )

    def test_get_questions(self):
        # Given
        user_list = [self.user1, self.user2]
        self.mock_core.user.get_all.return_value = user_list

        # When
        response, status_code = get_users()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "users" in response
        assert response["users"] == [self.user1.to_dict(), self.user2.to_dict()]
        self.mock_core.user.get_all.assert_called_with()

    def test_get_questions_with_status(self):
        # Given
        user_list = [self.user1, self.user2]
        self.mock_core.user.get_list_by_key.return_value = user_list
        kwargs = {
            "status": StatusEnum.READY
        }

        # When
        response, status_code = get_users(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "users" in response
        assert response["users"] == [self.user1.to_dict(), self.user2.to_dict()]
        self.mock_core.user.get_list_by_key.assert_called_with(status=StatusEnum.READY)


@pytest.mark.usefixtures("session")
class TestGetUserByUsername:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("controllers.user_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

    def test_get_user_by_username(self, user):
        # Given
        kwargs = {"username": user.username}
        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        response, status_code = get_user_by_username(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user.to_dict()
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_get_user_by_username_not_found(self, user):
        # Given
        kwargs = {"username": user.username}
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = get_user_by_username(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)


@pytest.mark.usefixtures("session")
class TestGetUserDetails:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("controllers.user_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        role_user = Role(id=1, name=RoleEnum.USER)
        role_admin = Role(id=2, name=RoleEnum.ADMIN)

        user.roles = [role_user]

        self.admin_user = User(
            id=2,
            username="admin",
            email="admin@email.com",
            password="adminpassword",
            salt="xyz",
            phone="0602030405",
            devices="['android']",
            status=StatusEnum.READY
        )
        self.admin_user.roles = [role_admin]

        self.mock_core.user.get_instance_by_key.side_effect = lambda username: (
            user if username == "username" else self.admin_user
        )

    def test_get_user_details_user_role(self, user):
        # Given
        kwargs = {"userId": user.id, "user": user.username}
        self.mock_core.user.get_instance_by_key.return_value = user
        self.mock_core.user.get_details.return_value = user.to_dict()

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user.to_dict()
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_core.user.get_details.assert_called_with(user.id)

    def test_get_user_details_user_role_not_allowed(self, user):
        # Given
        kwargs = {"userId": 10, "user": user.username}
        self.mock_core.user.get_instance_by_key.return_value = user
        self.mock_core.user.get_details.return_value = user.to_dict()

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 401
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_core.user.get_details.assert_called_with(10)

    def test_get_user_details_user_role_not_found(self, user):
        # Given
        kwargs = {"userId": user.id, "user": user.username}
        self.mock_core.user.get_instance_by_key.return_value = user
        self.mock_core.user.get_details.return_value = None

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_core.user.get_details.assert_called_with(user.id)

    def test_get_user_details_admin_role(self):
        # Given
        kwargs = {"userId": self.admin_user.id, "user": self.admin_user.username}
        self.mock_core.user.get_instance_by_key.return_value = self.admin_user
        self.mock_core.user.get_details.return_value = self.admin_user.to_dict()

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == self.admin_user.to_dict()
        self.mock_core.user.get_instance_by_key.assert_called_with(
            username=self.admin_user.username
        )
        self.mock_core.user.get_details.assert_called_with(self.admin_user.id)

    def test_get_user_details_user_invalid_role(self, user):
        # Given
        kwargs = {"userId": user.id, "user": user.username}
        user.roles = []
        self.mock_core.user.get_instance_by_key.return_value = user
        self.mock_core.user.get_details.return_value = user.to_dict()

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 401
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_core.user.get_details.assert_called_with(user.id)


@pytest.mark.usefixtures("session")
class TestPostUser:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        patch_core = patch("controllers.user_controller.tempo_core")
        self.mock_core = patch_core.start()
        request.addfinalizer(patch_core.stop)

        patch_get_user_info = patch(
            "controllers.user_controller.get_user_info"
        )
        self.mock_get_user_info = patch_get_user_info.start()
        request.addfinalizer(patch_get_user_info.stop)

        os.environ["PEPPER"] = "pepper"

        patch_hibp = patch.object(HibpClient, "check_breach")
        self.mock_hibp = patch_hibp.start()
        request.addfinalizer(patch_hibp.stop)

        patch_handle_email = patch(
            "controllers.user_controller.handle_email"
        )
        self.mock_handle_email = patch_handle_email.start()
        request.addfinalizer(patch_handle_email.stop)

        self.valid_kwargs = {
            "body": {
                "username": "username",
                "email": "username@email.com",
                "password": generate_password(
                    length=10,
                    use_upper=True,
                    use_lower=True,
                    use_digits=True,
                    allow_repetitions=False,
                    allow_series=False
                ),
                "questions": [
                    {
                        "questionId": 1,
                        "response": "answer"
                    }
                ],
                "device": "iphone",
                "phone": "123456789"
            }
        }
        self.question = Question(
            id=1,
            question="question?"
        )

        self.role = Role(
            id=1,
            name=RoleEnum.USER
        )

    def test_post_user(self, user):
        # Given
        kwargs = self.valid_kwargs
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_hibp.return_value = ["ok"]
        self.mock_core.user.create.return_value = user
        self.mock_core.role.get_instance_by_key.return_value = self.role

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 202
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user.to_dict()
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )
        self.mock_hibp.assert_called_once()
        self.mock_core.user.create.assert_called_once()
        self.mock_core.role.get_instance_by_key.assert_called_once_with(name=self.role.name)
        self.mock_core.user_role.create.assert_called_once_with(
            user_id=user.id,
            role_id=self.role.id
        )
        self.mock_core.user_questions.create.assert_called()
        self.mock_handle_email.assert_called_once_with(
            user_email=user.email,
            username=user.username,
            user_id=user.id
        )

    def test_post_user_question_wrong_input_question_id(self):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["questions"] = [{"response": "answer"}]

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_not_called()

    def test_post_user_question_wrong_input_response(self):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["questions"] = [{"questionId": 1}]

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_not_called()

    def test_post_user_question_not_found(self):
        # Given
        kwargs = self.valid_kwargs
        self.mock_core.question.get_by_id.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)

    def test_post_user_user_already_exists(self, user):
        # Given
        kwargs = self.valid_kwargs
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_post_user_invalid_password_length(self, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = generate_password(
            length=8,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            allow_repetitions=False,
            allow_series=False
        )
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_post_user_invalid_password_repetition(self, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = generate_password(
            length=10,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            allow_repetitions=True,
            allow_series=False
        )
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_post_user_invalid_password_series(self, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = generate_password(
            length=10,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            allow_repetitions=False,
            allow_series=True
        )
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_post_user_invalid_password_requirements(self, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = generate_password(
            length=10,
            use_upper=False,
            use_lower=True,
            use_digits=False,
            allow_repetitions=False,
            allow_series=False
        )
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    def test_post_user_invalid_password_personal_info(self, user):
        # Given
        password = generate_password(
            length=10,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            allow_repetitions=False,
            allow_series=False
        )
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = password
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = [password]

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )

    def test_post_user_insecure_password(self, user):
        # Given
        password = generate_password(
            length=10,
            use_upper=True,
            use_lower=True,
            use_digits=True,
            allow_repetitions=False,
            allow_series=False
        )

        hashed_password = (
            hashlib.sha1(password.encode("utf-8"))
            .hexdigest()
            .upper()
        )
        hash_end = hashed_password[5:]

        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = password
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_hibp.return_value = [f"{hash_end}:ok"]

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )
        self.mock_hibp.assert_called_once()

    def test_post_user_hibp_error(self, user):
        # Given
        kwargs = self.valid_kwargs
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_hibp.return_value = []

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 500
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )
        self.mock_hibp.assert_called_once()

    def test_post_user_email_error(self, user):
        # Given
        kwargs = self.valid_kwargs
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_hibp.return_value = ["ok"]
        self.mock_core.user.create.return_value = user
        self.mock_core.role.get_instance_by_key.return_value = self.role
        self.mock_handle_email.side_effect = smtplib.SMTPException

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 500
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )
        self.mock_hibp.assert_called_once()
        self.mock_core.user.create.assert_called_once()
        self.mock_core.role.get_instance_by_key.assert_called_once_with(name=self.role.name)
        self.mock_core.user_role.create.assert_called_once_with(
            user_id=user.id,
            role_id=self.role.id
        )
        self.mock_core.user_questions.create.assert_called()
        self.mock_handle_email.assert_called_once_with(
            user_email=user.email,
            username=user.username,
            user_id=user.id
        )


@pytest.mark.usefixtures("session")
class TestGetUserInfo:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_generate_substrings = patch(
            "controllers.user_controller.generate_substrings"
        )
        self.mock_generate_substrings = (
            self.patch_generate_substrings.start()
        )
        request.addfinalizer(self.patch_generate_substrings.stop)

    def test_get_user_info(self):
        # Given
        username = "username"
        email = "email@fake.com"
        self.mock_generate_substrings.return_value = ["sub"]

        # When
        response = get_user_info(username, email)

        # Then
        assert response == {
            "fake",
            "sub"
        }


@pytest.mark.usefixtures("session")
class TestGenerateSubstrings:

    def test_get_user_info(self):
        # Given
        word = "substring"

        # When
        response = generate_substrings(word)

        # Then
        assert response == [
            "subs",
            "subst",
            "substr",
            "substri",
            "substrin",
            "substring"
        ]
