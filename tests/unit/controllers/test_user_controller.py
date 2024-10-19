from unittest.mock import patch
import pytest
import secrets
import string

from controllers.user_controller import (generate_substrings,
                                         get_user_by_username,
                                         get_user_details, get_user_info,
                                         get_users, patch_user, post_users)
from models.user import StatusEnum


def generate_password(
        length=10,
        use_upper=True,
        use_lower=True,
        use_digits=True,
        allow_repetitions=False,
        allow_series=False
):
    # Construction des caractères disponibles en fonction des critères
    available_chars = ""
    if use_upper:
        available_chars += string.ascii_uppercase
    if use_lower:
        available_chars += string.ascii_lowercase
    if use_digits:
        available_chars += string.digits

    # Vérification des options sélectionnées
    if not available_chars:
        raise ValueError("At least one character type must be selected.")

    # Fonction pour vérifier les séries (abc, 123, etc.)
    def has_series(password):
        for i in range(len(password) - 2):
            if (ord(password[i + 1]) - ord(password[i]) == 1) and (ord(password[i + 2]) - ord(password[i + 1]) == 1):
                return True
        return False

    # Fonction pour vérifier les répétitions (ex: xxx)
    def has_repetitions(password):
        return any(password[i] == password[i + 1] == password[i + 2] for i in range(len(password) - 2))

    password = ""

    while not password or \
            (allow_series and not has_series(password)) or \
            (allow_repetitions and not has_repetitions(password)) or \
            (not allow_series and has_series(password)) or \
            (not allow_repetitions and has_repetitions(password)):

        password = []

        # Ajout forcé d'au moins une majuscule, une minuscule et un chiffre si requis
        if use_upper:
            password.append(secrets.choice(string.ascii_uppercase))
        if use_lower:
            password.append(secrets.choice(string.ascii_lowercase))
        if use_digits:
            password.append(secrets.choice(string.digits))

        # Compléter le reste du mot de passe avec des caractères aléatoires
        while len(password) < length:
            password.append(secrets.choice(available_chars))

        # Convertir en chaîne de caractères
        password = ''.join(password)

    # Si les répétitions ne sont pas autorisées, on vérifie qu'il n'y en a pas
    if not allow_repetitions:
        while has_repetitions(password):
            password = ''.join(secrets.choice(available_chars) for _ in range(length))

    # Si les séries ne sont pas autorisées, on vérifie qu'il n'y en a pas
    if not allow_series:
        while has_series(password):
            password = ''.join(secrets.choice(available_chars) for _ in range(length))

    return password


@pytest.mark.usefixtures("session")
class TestGetUsers:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_user_list = patch(
            "controllers.user_controller.user_list"
        )
        self.mock_user_list = self.patch_user_list.start()
        request.addfinalizer(self.patch_user_list.stop)

    def test_get_questions(self):
        # Given
        user_list = ["Question 1", "Question 2", "Question 3"]
        self.mock_user_list.return_value = user_list

        # When
        response, status_code = get_users()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "users" in response
        assert response["users"] == user_list
        self.mock_user_list.assert_called_with()

    def test_get_questions_empty_output(self):
        # Given
        self.mock_user_list.return_value = None

        # When
        response, status_code = get_users()

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "users" in response
        assert response["users"] == []
        self.mock_user_list.assert_called_with()


@pytest.mark.usefixtures("session")
class TestGetUserByUsername:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_username = patch(
            "controllers.user_controller.get_by_username"
        )
        self.mock_get_by_username = self.patch_get_by_username.start()
        request.addfinalizer(self.patch_get_by_username.stop)

    def test_get_user_by_username(self):
        # Given
        username_str = "username"
        kwargs = {"username": username_str}
        user = {"id": 1, "username": username_str}
        self.mock_get_by_username.return_value = user

        # When
        response, status_code = get_user_by_username(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user
        self.mock_get_by_username.assert_called_with(username_str)

    def test_get_user_by_username_no_kwargs(self):
        # When
        response, status_code = get_user_by_username()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_username.assert_not_called()

    def test_get_user_by_username_not_found(self):
        # Given
        username_str = "username"
        kwargs = {"username": username_str}
        self.mock_get_by_username.return_value = None

        # When
        response, status_code = get_user_by_username(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_username.assert_called_with(username_str)


@pytest.mark.usefixtures("session")
class TestGetUserDetails:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_details = patch(
            "controllers.user_controller.get_details"
        )
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

    def test_get_user_details(self):
        # Given
        id = 1
        kwargs = {"userId": id}
        user = {"id": 1, "username": "username"}
        self.mock_get_details.return_value = user

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user
        self.mock_get_details.assert_called_with(id)

    def test_get_user_details_no_kwargs(self):
        # When
        response, status_code = get_user_details()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_details.assert_not_called()

    def test_get_user_details_not_found(self):
        # Given
        username_str = "username"
        kwargs = {"userId": username_str}
        self.mock_get_details.return_value = None

        # When
        response, status_code = get_user_details(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_details.assert_called_with(username_str)


@pytest.mark.usefixtures("session")
class TestPatchUser:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_details = patch(
            "controllers.user_controller.get_details"
        )
        self.mock_get_details = self.patch_get_details.start()
        request.addfinalizer(self.patch_get_details.stop)

        self.patch_update = patch("controllers.user_controller.update")
        self.mock_update = self.patch_update.start()
        request.addfinalizer(self.patch_update.stop)

    def test_patch_user(self):
        # Given
        id = 1
        status = StatusEnum.READY
        kwargs = {
            "userId": id,
            "body": {
                "status": status
            }
        }
        user = {"id": 1, "username": "username", "status": status}
        self.mock_update.return_value = user

        # When
        response, status_code = patch_user(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user
        self.mock_get_details.assert_not_called()
        self.mock_update.assert_called_with(id, status)

    def test_patch_user_no_kwargs(self):
        # When
        response, status_code = patch_user()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_details.assert_not_called()
        self.mock_update.assert_not_called()

    def test_patch_user_invalid_kwargs(self):
        # Given
        id = 1
        kwargs = {
            "userId": id,
        }

        # When
        response, status_code = patch_user(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_details.assert_not_called()
        self.mock_update.assert_not_called()

    def test_patch_user_no_status(self):
        # Given
        id = 1
        kwargs = {
            "userId": id,
            "body": {
                "something": "useless"
            }
        }
        user = {
            "id": 1,
            "username": "username",
            "email": "fake@gmail.com"
        }
        self.mock_get_details.return_value = user

        # When
        response, status_code = patch_user(**kwargs)

        # Then
        assert status_code == 200
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user
        self.mock_get_details.assert_called_with(id)
        self.mock_update.assert_not_called()

    def test_patch_user_not_found(self):
        # Given
        id = 1
        status = StatusEnum.READY
        kwargs = {
            "userId": id,
            "body": {
                "status": status
            }
        }
        self.mock_update.return_value = None

        # When
        response, status_code = patch_user(**kwargs)

        # Then
        assert status_code == 404
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_details.assert_not_called()
        self.mock_update.assert_called_with(id, status)


@pytest.mark.usefixtures("session")
class TestPostUser:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_get_by_id = patch(
            "controllers.user_controller.get_by_id"
        )
        self.mock_get_by_id = self.patch_get_by_id.start()
        request.addfinalizer(self.patch_get_by_id.stop)

        self.patch_get_by_username = patch(
            "controllers.user_controller.get_by_username"
        )
        self.mock_get_by_username = self.patch_get_by_username.start()
        request.addfinalizer(self.patch_get_by_username.stop)

        self.patch_get_user_info = patch(
            "controllers.user_controller.get_user_info"
        )
        self.mock_get_user_info = self.patch_get_user_info.start()
        request.addfinalizer(self.patch_get_user_info.stop)

        self.patch_env_variable = patch(
            "controllers.user_controller.os.environ.get"
        )
        self.mock_env_variable = self.patch_env_variable.start()
        request.addfinalizer(self.patch_env_variable.stop)

        self.patch_call_to_api = patch(
            "controllers.user_controller.call_to_api"
        )
        self.mock_call_to_api = self.patch_call_to_api.start()
        request.addfinalizer(self.patch_call_to_api.stop)

        self.patch_create = patch("controllers.user_controller.create")
        self.mock_create = self.patch_create.start()
        request.addfinalizer(self.patch_create.stop)

        self.patch_add_question_to_user = patch(
            "controllers.user_controller.add_question_to_user"
        )
        self.mock_add_question_to_user = (
            self.patch_add_question_to_user.start()
        )
        request.addfinalizer(self.patch_add_question_to_user.stop)

        self.patch_handle_email = patch(
            "controllers.user_controller.handle_email"
        )
        self.mock_handle_email = self.patch_handle_email.start()
        request.addfinalizer(self.patch_handle_email.stop)

    def test_post_user(self):
        # Given
        status = StatusEnum.READY
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
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
        user = {"id": 1, "username": "username", "status": status}
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_call_to_api.text.return_value = "ok"
        self.mock_create.return_value = user
        self.mock_env_variable.return_value = "pepper"

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 202
        assert isinstance(response, dict)
        assert "user" in response
        assert response["user"] == user
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_called_with(
            "username",
            "fake@email.com"
        )
        self.mock_env_variable.assert_called()
        self.mock_call_to_api.assert_called()
        self.mock_create.assert_called_once()
        self.mock_add_question_to_user.assert_called()

    def test_post_user_no_payload(self):
        # When
        response, status_code = post_users()

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_username(self):
        # Given
        kwargs = {
            "body": {
                "email": "fake@email.com",
                "password": "azertyAA2",
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

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_email(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "password": "azertyAA2",
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

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_password(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
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

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_questions(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
                "device": "iphone",
                "phone": "123456789"
            }
        }

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_device(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
                "questions": [
                    {
                        "questionId": 1,
                        "response": "answer"
                    }
                ],
                "phone": "123456789"
            }
        }

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_phone(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
                "questions": [
                    {
                        "questionId": 1,
                        "response": "answer"
                    }
                ],
                "device": "iphone",
            }
        }

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_question_id(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
                "questions": [
                    {
                        "response": "answer"
                    }
                ],
                "device": "iphone",
                "phone": "123456789"
            }
        }

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_payload_question_response(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
                "questions": [
                    {
                        "questionId": 1,
                    }
                ],
                "device": "iphone",
                "phone": "123456789"
            }
        }

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_not_called()
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_question_not_found(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
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
        self.mock_get_by_id.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_not_called()
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_username_exists(self):
        # Given
        status = StatusEnum.READY
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
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
        user = {"id": 1, "username": "username", "status": status}
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = user

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_password_repetition(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "aaazertyAA2",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_password_serie(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "abczertyAA2",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_invalid_password_requirements(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azerty",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_not_called()
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_insecure_password(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "usernameA42",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_called_with(
            "username",
            "fake@email.com"
        )
        self.mock_env_variable.assert_not_called()
        self.mock_call_to_api.assert_not_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_api_call_failed(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_call_to_api.return_value = None

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 500
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_called_with(
            "username",
            "fake@email.com"
        )
        self.mock_env_variable.assert_called()
        self.mock_call_to_api.assert_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_previously_hacked_password(self):
        # Given
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
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
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_call_to_api.return_value.text.splitlines.return_value = [
            "8E91F26BB90232FC6A1374E750B4FE04BE1:ok"
        ]
        self.mock_env_variable.return_value = "pepper"

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_called_with(
            "username",
            "fake@email.com"
        )
        self.mock_env_variable.assert_called()
        self.mock_call_to_api.assert_called()
        self.mock_create.assert_not_called()
        self.mock_add_question_to_user.assert_not_called()

    def test_post_user_handle_email_exception(self):
        # Given
        status = StatusEnum.READY
        kwargs = {
            "body": {
                "username": "username",
                "email": "fake@email.com",
                "password": "azertyAA2",
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
        user = {"id": 1, "username": "username", "status": status}
        self.mock_get_by_id.return_value = {
            "id": 1
        }
        self.mock_get_by_username.return_value = None
        self.mock_get_user_info.return_value = ["username", "fake"]
        self.mock_call_to_api.text.return_value = "ok"
        self.mock_create.return_value = user
        self.mock_env_variable.return_value = "pepper"
        self.mock_handle_email.side_effect = Exception("email error")

        # When
        response, status_code = post_users(**kwargs)

        # Then
        assert status_code == 400
        assert isinstance(response, dict)
        assert "message" in response
        assert response["message"] == "Verification email cannot be send"
        self.mock_get_by_id.assert_called_with(1)
        self.mock_get_by_username.assert_called_with("username")
        self.mock_get_user_info.assert_called_with(
            "username",
            "fake@email.com"
        )
        self.mock_env_variable.assert_called()
        self.mock_call_to_api.assert_called()
        self.mock_create.assert_called_once()
        self.mock_add_question_to_user.assert_called()
        self.mock_handle_email.assert_called_with(
            user_email="fake@email.com",
            username="username",
            user_id=1
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
