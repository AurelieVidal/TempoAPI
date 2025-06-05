import hashlib
import json
import os
import smtplib
from unittest.mock import patch, call

import pytest

from adapters.hibp_client import HibpClient
from controllers.user_controller import (generate_substrings,
                                         get_user_by_username,
                                         get_user_details, get_user_info,
                                         get_users, post_users, reset_password, generate_salt)
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
            "controllers.user_controller.handle_email_create_user"
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

    @patch("controllers.user_controller.generate_salt")
    def test_post_user(self, mock_salt, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = "Gu8mpzc336Sab"
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_hibp.return_value = ["ok"]
        self.mock_core.user.create.return_value = user
        self.mock_core.role.get_instance_by_key.return_value = self.role
        pepper = os.environ.get("PEPPER")
        mock_salt.return_value = "abcd"

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
        self.mock_core.user.create.assert_called_once_with(
            username=kwargs.get("body").get("username"),
            email=kwargs.get("body").get("email"),
            password=hashlib.sha256(
                (
                    pepper + kwargs.get("body").get("password") + "abcd"
                ).encode("utf-8")).hexdigest().upper(),
            salt="abcd",
            devices=json.dumps([kwargs.get("body").get("device")]),
            status=StatusEnum.CHECKING_EMAIL,
            phone=kwargs.get("body").get("phone")
        )
        self.mock_core.role.get_instance_by_key.assert_called_once_with(name=self.role.name)
        self.mock_core.user_role.create.assert_called_once_with(
            user_id=user.id,
            role_id=self.role.id
        )
        self.mock_core.user_questions.create.assert_called_with(
            user_id=user.id,
            question_id=1,
            response=hashlib.sha256(
                (pepper + "answer" + "abcd").encode("utf-8")).hexdigest().upper()
        )
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
        assert response["message"] == ("Input error, for each question you have "
                                       "to provide the questionId and the answer")
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
        assert response["message"] == "Username is already used"
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
        assert response["message"] == "Password length should be minimum 10."
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
        assert response["message"] == "You cannot have 3 identical characters in a row."
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
        assert response["message"] == "Sequence longer than 3 characters detected."
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)

    @pytest.mark.parametrize(
        "password",
        [
            "ONLYUPPERCASE",
            "onlylowercase",
            "16584236951775",
            "lower129638532",
            "lowerUPPER",
            "UPPER632984621354",
        ]
    )
    def test_post_user_invalid_password_requirements(self, password, user):
        # Given
        kwargs = self.valid_kwargs
        kwargs["body"]["password"] = password
        self.mock_core.question.get_by_id.return_value = self.question
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        assert response["message"] == ("Password must have a number, an uppercase letter, "
                                       "and a lowercase letter.")
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
        assert response["message"] == "Password seems to contain personal information."
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
        assert response["message"] == "Password is too weak."
        self.mock_core.question.get_by_id.assert_called_with(self.question.id)
        self.mock_core.user.get_instance_by_key.assert_called_with(username=user.username)
        self.mock_get_user_info.assert_called_with(
            user.username,
            user.email
        )
        self.mock_hibp.assert_called_once_with(
            hashlib.sha1(password.encode("utf-8")).hexdigest().upper()[:5]
        )

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
        assert response["message"] == "Password checking feature is unavailable."
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

    def test_generate_salt(self):
        # When
        salt = generate_salt()

        # Then
        assert len(salt) == 5
        assert all("A" <= c <= "Z" or "a" <= c <= "z" for c in salt)

    def test_generate_salt_patch_random(self):
        # When
        with patch(
                "controllers.user_controller.random.randint", side_effect=[1, 65, 0, 97]
        ) as patch_random:
            salt = generate_salt(length=2)

            # Then
            expected_calls = [
                call(0, 1),
                call(65, 90),
                call(0, 1),
                call(97, 122)
            ]
            assert patch_random.call_args_list == expected_calls

        assert "A" in salt

    def test_get_user_infos(self):

        # When
        list_info = get_user_info("user", "great.mail@email.com")

        # Then
        assert list_info == {"email", "grea", "great", "mail", "user"}

    def test_get_user_infos_short_username(self):

        # When
        list_info = get_user_info("us", "great.mail@email.com")

        # Then
        assert list_info == {"email", "grea", "great", "mail"}


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


@pytest.mark.usefixtures("session")
class TestResetPassword:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, user):
        self.patch_core = patch("controllers.user_controller.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_check_password = patch("controllers.user_controller.check_password")
        self.mock_check_password = self.patch_check_password.start()
        request.addfinalizer(self.patch_check_password.stop)

        self.patch_handle_email_password_changed = patch(
            "controllers.user_controller.handle_email_password_changed"
        )
        self.mock_handle_email_password_changed = self.patch_handle_email_password_changed.start()
        request.addfinalizer(self.patch_handle_email_password_changed.stop)

        role_user = Role(id=1, name=RoleEnum.USER)
        user.roles = [role_user]
        self.user = user

        os.environ["PEPPER"] = "pepper"

        self.kwargs = {
            "user": self.user.username,
            "userId": self.user.id,
            "body": {
                "newPassword": "new_password"
            }
        }

    def test_reset_password(self):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = None
        pepper = os.environ.get("PEPPER")
        new_password = pepper + "new_password" + self.user.salt
        new_password = hashlib.sha256(new_password.encode("utf-8")).hexdigest().upper()

        # When
        response, status_code = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_called_once_with(self.user.id, password=new_password)
        self.mock_core.user.get_instance_by_key.assert_called_once_with(username=self.user.username)
        self.mock_check_password.assert_called_once_with(
            password="new_password",
            username=self.user.username,
            email=self.user.email
        )
        self.mock_handle_email_password_changed.assert_called_once_with(self.user)
        assert status_code == 200
        assert isinstance(response, dict)
        assert response == {"message": "The password has been successfully reset"}

    def test_reset_password_admin_user(self):
        # Given
        role_admin = Role(id=2, name=RoleEnum.ADMIN)
        self.user.roles = [role_admin]

        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = None

        # When
        response, status_code = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_called_once()
        self.mock_handle_email_password_changed.assert_called_once_with(self.user)
        assert status_code == 200
        assert isinstance(response, dict)
        assert (
            response
            == {"message": f"The password of user {self.user.username} has been successfully reset"}
        )

    def test_reset_password_user_not_found(self):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response, status_code = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_not_called()
        self.mock_handle_email_password_changed.assert_not_called()
        assert status_code == 404
        assert isinstance(response, dict)
        assert response == {"message": f"User with id {self.user.id} not found"}

    def test_reset_password_password_not_valid(self):
        # Given
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = "error"

        # When
        response = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_not_called()
        self.mock_handle_email_password_changed.assert_not_called()
        assert response == "error"

    def test_reset_password_same_password(self):
        # Given

        pepper = os.environ["PEPPER"]
        same_password_hash = hashlib.sha256(
            (pepper + "new_password" + self.user.salt).encode("utf-8")
        ).hexdigest().upper()
        self.user.password = same_password_hash

        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = None

        # When
        response, status_code = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_not_called()
        self.mock_handle_email_password_changed.assert_not_called()
        assert status_code == 400
        assert isinstance(response, dict)
        assert response == {"message": "You cannot use the same password"}

    def test_reset_password_unauthorized(self):
        # Given
        kwargs = {
            "username": self.user.username,
            "userId": self.user.id + 1,
            "body": {
                "newPassword": "new_password"
            }
        }
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = None

        # When
        response, status_code = reset_password(**kwargs)

        # Then
        self.mock_core.user.update.assert_not_called()
        self.mock_handle_email_password_changed.assert_not_called()
        assert status_code == 401
        assert isinstance(response, dict)
        assert (
            response["message"]
            == f"You don't have the permission to see information of user {self.user.id +1}"
        )

    def test_reset_password_no_required_role(self):
        # Given
        self.user.roles = []
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_check_password.return_value = None

        # When
        response, status_code = reset_password(**self.kwargs)

        # Then
        self.mock_core.user.update.assert_not_called()
        self.mock_handle_email_password_changed.assert_not_called()
        assert status_code == 401
        assert isinstance(response, dict)
        assert (
            response["message"]
            == f"User {self.user.id} does not have the required role to execute this action"
        )
