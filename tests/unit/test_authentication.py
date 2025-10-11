import base64
import hashlib
import json
import os
import smtplib
from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock, patch

import jwt
import pytest
from freezegun import freeze_time

from authentication import (basic_auth, check_is_suspicious, check_route,
                            jwt_auth)
from core.models import (Connection, ConnectionStatusEnum, Question,
                         StatusEnum, UserQuestion)


@pytest.mark.usefixtures("session")
class TestBasicAuth:

    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("authentication.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.pepper = "pepper"
        os.environ["PEPPER"] = self.pepper

    def test_basic_auth(self, user):
        # Given
        username_input = "username"
        password_input = "password"
        to_encode = self.pepper + password_input + user.salt
        hashed_password = hashlib.sha256(
            to_encode.encode("utf-8")
        ).hexdigest().upper()
        user.password = hashed_password
        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        response = basic_auth(username_input, password_input)

        # Then
        self.mock_core.user.get_instance_by_key.assert_called_once_with(username=username_input)
        assert response == {"sub": username_input}

    def test_basic_auth_wrong_input_username(self):
        # Given
        username_input = ""
        password_input = "password"

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_wrong_input_password(self):
        # Given
        username_input = "username"
        password_input = ""

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    def test_basic_auth_user_not_found(self):
        # Given
        username_input = "username"
        password_input = "password"
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response = basic_auth(username_input, password_input)

        # Then
        assert not response

    @freeze_time(datetime.now())
    def test_basic_auth_wrong_password(self, user):
        # Given
        username_input = "username"
        password_input = "password"
        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        response = basic_auth(username_input, password_input)

        # Then
        self.mock_core.connection.create.assert_called_once_with(
            user_id=user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.FAILED
        )
        assert not response


@pytest.mark.usefixtures("session")
class TestJwtAuth:
    @pytest.fixture(autouse=True)
    def setup_method(self, request):
        self.patch_core = patch("authentication.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        os.environ["SECRET_KEY"] = "SECRET"
        self.key = os.environ["SECRET_KEY"]

    def test_jwt_auth_valid_token(self):
        # Given
        payload = {
            "username": "john",
            "exp": datetime.now().timestamp() + 3600
        }
        token = jwt.encode(payload, self.key)

        # When
        result = jwt_auth(token)

        # Then
        assert result == {"sub": "john"}

    @freeze_time(datetime.now())
    def test_jwt_auth_expired_token(self, user):
        # Given
        payload = {
            "username": "john",
            "exp": datetime.now().timestamp() - 10
        }
        token = jwt.encode(payload, self.key)

        self.mock_core.user.get_instance_by_key.return_value = user

        # When
        result = jwt_auth(token)

        # Then
        self.mock_core.user.get_instance_by_key.assert_called_once_with("john")
        self.mock_core.connection.create.assert_called_once_with(
            user_id=user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.FAILED
        )
        assert result is None

    def test_jwt_auth_invalid_signature(self):
        # Given
        payload = {"username": "john", "exp": datetime.now().timestamp() + 100}
        token = jwt.encode(payload, "WRONG_KEY")

        # When
        result = jwt_auth(token)

        # Then
        assert result is None


@pytest.mark.usefixtures("session")
class TestCheckIsSuspicious:

    @pytest.fixture(autouse=True)
    def setup_method(self, request, connection):
        self.patch_core = patch("authentication.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        connection.date = datetime.now()
        self.connection = connection

    @freeze_time(datetime.now())
    def test_check_is_suspicious(self, user):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            []
        ]
        device = json.loads(user.devices)[0]
        self.connection.date = datetime.now() - timedelta(days=30)

        # When
        response = check_is_suspicious(user, device, "0.0.0.0")

        # Then
        assert not response
        first_call_args = self.mock_core.connection.get_list_by_key.call_args_list[0]
        second_call_args = self.mock_core.connection.get_list_by_key.call_args_list[1]
        assert first_call_args == mock.call(
            order_by=Connection.date,
            limit=1,
            order="desc",
            user_id=user.id
        )
        assert second_call_args == mock.call(
            order_by=Connection.date,
            limit=5,
            order="desc",
            user_id=user.id
        )

    def test_check_is_suspicious_first_connection(self, user):
        # Given
        self.mock_core.connection.get_list_by_key.return_value = []
        device = json.loads(user.devices)[0]

        # When
        response = check_is_suspicious(user, device, "0.0.0.0")

        # Then
        assert not response

    def test_check_is_suspicious_last_connection_validated(self, user):
        # Given
        self.connection.status = ConnectionStatusEnum.VALIDATED
        self.mock_core.connection.get_list_by_key.return_value = [self.connection]
        device = json.loads(user.devices)[0]

        # When
        response = check_is_suspicious(user, device, "0.0.0.0")

        # Then
        assert not response
        self.mock_core.user.update.assert_called_with(user.id, devices='["iphone", "iphone"]')

    def test_check_is_suspicious_last_conn_date_one_month(self, user):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            []
        ]
        device = json.loads(user.devices)[0]
        self.connection.date = datetime.now() - timedelta(days=30, hours=10)

        # When
        response = check_is_suspicious(user, device, "0.0.0.0")

        # Then
        assert response

    def test_check_is_suspicious_unknowned_device(self, user):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            []
        ]

        # When
        response = check_is_suspicious(user, "unknowned", "0.0.0.0")

        # Then
        assert response

    def test_check_is_suspicious_5_time_error(self, user):
        # Given
        self.connection.status = ConnectionStatusEnum.FAILED
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            [self.connection, self.connection, self.connection, self.connection, self.connection]
        ]
        device = json.loads(user.devices)[0]

        # When
        response = check_is_suspicious(user, device, "0.0.0.0")

        # Then
        assert response

    @freeze_time(datetime.now())
    def test_check_is_suspicious_ip_changed(self, user):
        # Given
        self.connection.date = datetime.now() - timedelta(minutes=59)
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            []
        ]
        device = json.loads(user.devices)[0]

        # When
        response = check_is_suspicious(user, device, "0.0.0.1")

        # Then
        assert response

    @freeze_time(datetime.now())
    def test_check_is_suspicious_ip_changed_after_an_hour(self, user):
        # Given
        self.connection.date = datetime.now() - timedelta(hours=1)
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
            []
        ]
        device = json.loads(user.devices)[0]

        # When
        response = check_is_suspicious(user, device, "0.0.0.1")

        # Then
        assert not response


@pytest.mark.usefixtures("session")
class TestBeforeRequest:

    @pytest.fixture(autouse=True)
    def setup(self, request, client, user, connection):
        self.question = Question(id=1, question="What is your favorite color?")
        user_question = UserQuestion(
            user_id=user.id,
            question=self.question,
            response="abcd"
        )
        user.questions = [user_question]
        self.client = client
        self.user = user
        self.connection = connection

        self.patch_core = patch("authentication.tempo_core")
        self.mock_core = self.patch_core.start()
        request.addfinalizer(self.patch_core.stop)

        self.patch_paths = patch(
            "authentication.SECURE_PATHS", ["GET /test_func", "GET /test_func/{id}"]
        )
        self.mock_paths = self.patch_paths.start()
        request.addfinalizer(self.patch_paths.stop)

        self.patch_check = patch("authentication.check_is_suspicious", return_value=False)
        self.mock_check = self.patch_check.start()
        request.addfinalizer(self.patch_check.stop)

        self.patch_handle_email = patch("authentication.handle_email_suspicious_connection")
        self.mock_handle_email = self.patch_handle_email.start()
        request.addfinalizer(self.patch_handle_email.stop)

    def get_auth_header(self):
        credentials = f"{self.user.username}:password"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def get_bearer_header(self, username=None):
        """Helper pour générer un token JWT"""
        username = username or self.user.username
        payload = {
            "username": username,
            "exp": datetime.now() + timedelta(minutes=30)
        }
        token = jwt.encode(payload, os.environ["SECRET_KEY"])
        return f"Bearer {token}"

    @pytest.mark.parametrize("auth_type", ["basic", "bearer"])
    @freeze_time(datetime.now())
    def test_before_request(self, auth_type):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user

        if auth_type == "basic":
            auth_header = self.get_auth_header()
        else:
            auth_header = self.get_bearer_header()

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": auth_header,
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 200
        self.mock_core.connection.create.assert_called_once_with(
            user_id=self.user.id,
            date=datetime.now(),
            device="iphone",
            ip_address="127.0.0.1",
            status=ConnectionStatusEnum.SUCCESS
        )

    @freeze_time(datetime.now())
    def test_before_request_user_not_found(self):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
        ]
        self.mock_core.user.get_instance_by_key.return_value = None

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 404

    def test_before_request_no_secure_route(self):
        # When
        response = self.client.get("/test_fake", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 200
        self.mock_core.connection.create.assert_not_called()

    def test_before_request_user_banned(self):
        # Given
        self.user.status = StatusEnum.BANNED
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 429
        self.mock_core.connection.create.assert_not_called()

    def test_before_request_missing_device_header(self):
        # Given
        self.mock_core.connection.get_list_by_key.side_effect = [
            [self.connection],
        ]
        self.mock_core.user.get_instance_by_key.return_value = self.user

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
        })

        # Then
        assert response.status_code == 403
        self.mock_core.connection.create.assert_not_called()

    @freeze_time(datetime.now())
    def test_before_request_first_connection(self):
        # Given
        self.mock_core.connection.get_list_by_key.return_value = []
        self.mock_core.user.get_instance_by_key.return_value = self.user

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 200
        self.mock_core.connection.create.assert_called_once_with(
            user_id=self.user.id,
            date=datetime.now(),
            device="iphone",
            ip_address="127.0.0.1",
            status=ConnectionStatusEnum.SUCCESS
        )

    @freeze_time(datetime.now())
    def test_before_request_create_suspicious(self):
        # Given
        self.mock_check.return_value = True
        self.mock_core.connection.get_list_by_key.return_value = [self.connection]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_core.connection.create.return_value = self.connection

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 412
        self.mock_handle_email.assert_called_once_with(user=self.user, connection=self.connection)
        self.mock_core.connection.create.assert_called_once_with(
            user_id=self.user.id,
            date=datetime.now(),
            device="iphone",
            ip_address="127.0.0.1",
            status=ConnectionStatusEnum.SUSPICIOUS,
            output=json.dumps({
                "message": "suspicious connexion",
                "question": self.question.question
            }, ensure_ascii=False)
        )

    @freeze_time(datetime.now())
    def test_before_request_create_suspicious_no_new_conn(self):
        # Given
        self.mock_check.return_value = True
        self.connection.status = ConnectionStatusEnum.SUSPICIOUS
        self.connection.date = datetime.now()
        self.mock_core.connection.get_list_by_key.return_value = [self.connection]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_core.connection.create.return_value = self.connection

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 412
        self.mock_handle_email.assert_not_called()
        self.mock_core.connection.create.assert_not_called()

    @freeze_time(datetime.now())
    def test_before_request_create_suspicious_error_email(self):
        # Given
        self.mock_check.return_value = True
        self.mock_core.connection.get_list_by_key.return_value = [self.connection]
        self.mock_core.user.get_instance_by_key.return_value = self.user
        self.mock_core.connection.create.return_value = self.connection
        self.mock_handle_email.side_effect = smtplib.SMTPException("error")

        # When
        response = self.client.get("/test_func", headers={
            "Authorization": self.get_auth_header(),
            "Device": "iphone"
        })

        # Then
        assert response.status_code == 500
        self.mock_handle_email.assert_called_once_with(user=self.user, connection=self.connection)
        self.mock_core.connection.create.assert_called_once_with(
            user_id=self.user.id,
            date=datetime.now(),
            device="iphone",
            ip_address="127.0.0.1",
            status=ConnectionStatusEnum.SUSPICIOUS,
            output=json.dumps({
                "message": "suspicious connexion",
                "question": self.question.question
            }, ensure_ascii=False)
        )

    def test_check_route(self):
        # Given
        mock_request = MagicMock(rule="/test_func")

        # When
        route = check_route(mock_request, "GET")

        # Then
        assert route == "GET /test_func"

    def test_check_route_with_arg(self):
        # Given
        mock_request = MagicMock(rule="/test_func/<id>")

        # When
        route = check_route(mock_request, "GET")

        # Then
        assert route == "GET /test_func/{id}"

    def test_check_route_no_url_rule(self):
        # When
        route = check_route(None, "GET")

        # Then
        assert not route

    def test_check_route_no_secure_route(self):
        # Given
        mock_request = MagicMock(rule="/test_fake")

        # When
        route = check_route(mock_request, "GET")

        # Then
        assert not route
