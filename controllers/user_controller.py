import hashlib
import json
import os
import random
import re
import smtplib

from adapters.hibp_client import HibpClient
from core.models.role import RoleEnum
from core.models.user import StatusEnum
from core.tempo_core import tempo_core
from utils.utils import handle_email


def get_users(**kwargs):
    """
    GET /users

    Params :
        - status in kwargs, to filter users on status
    :return: The list of all users
    """
    status = kwargs.get("status")

    if status:
        users = tempo_core.user.get_list_by_key(status=status)
    else:
        users = tempo_core.user.get_all()
    output = [user.to_dict() for user in users]

    return {"users": output}, 200


def get_user_by_username(**kwargs):
    """
    GET /users/{username}

    Params :
        - username in kwargs, to filter users on username
    :return: The user if it exists
    """

    username = kwargs.get("username")

    user = tempo_core.user.get_instance_by_key(username=username)
    if not user:
        return {"message": f"Username '{username}' not found"}, 404

    return {"user": user.to_dict()}, 200


def get_user_details(**kwargs):
    """
    GET /users/{userId}/details

    Params :
        - userId in kwargs, to filter users on their id
    :return: All detail information about a user
    """
    user_id = kwargs.get("userId")
    username = kwargs.get("user")
    user = tempo_core.user.get_instance_by_key(username=username)

    user_roles = [role.name for role in user.roles]

    output = tempo_core.user.get_details(user_id)
    if not output:
        return {"message": f"User {user_id} not found or incomplete"}, 404

    # If user has ADMIN role, they can view the information for all users
    if RoleEnum.ADMIN in user_roles:
        return {"user": output}, 200

    # If user has only USER role, they can view the information for them
    if RoleEnum.USER in user_roles:
        if int(user_id) != user.id:
            return {
                "message": f"You don't have the permission to see information of user {user_id}"
            }, 401
        return {"user": output}, 200

    return {
        "message": f"User {user_id} does not have the required role to execute this action"
    }, 401


def post_users(**kwargs):
    """
    POST /users

    Params :
        - username in kwargs, the chosen username
        - email in kwargs, the email of the user
        - password in kwargs, the password chosen by the user
        - phone in kwargs, the phone number of the user
        - questions in kwargs, the list of questions answered by the user : questionId and response
        - device in kwargs, the device used by the user to create his account

    :return: The created user
    """

    payload = kwargs.get("body")
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    questions = payload.get("questions")

    # Check if questions exists
    for question in questions:
        question_id = question.get("questionId")
        response = question.get("response")
        if not question_id or not response:
            return {
                "message":
                    "Input error, for each question you have to provide "
                    "the questionId and the answer"
            }, 400

        if not tempo_core.question.get_by_id(question_id):
            return {"message": f"Question {question_id} not found"}, 404

    # Check username
    if tempo_core.user.get_instance_by_key(username=username):
        return {"message": "Username is already used"}, 400

    check = check_password(password=password, username=username, email=email)
    if check is not None:
        return check

    salt = generate_salt()

    # Hash the password
    pepper = os.environ.get("PEPPER")
    password = pepper + password + salt
    password = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()

    # Create the user
    user = tempo_core.user.create(
        username=username,
        email=email,
        password=password,
        salt=salt,
        devices=json.dumps([payload.get("device")]),
        status=StatusEnum.CHECKING_EMAIL,
        phone=payload.get("phone")
    )

    # Assign to the created user default role : USER
    default_role = tempo_core.role.get_instance_by_key(name=RoleEnum.USER)
    tempo_core.user_role.create(user_id=user.id, role_id=default_role.id)

    # Associate questions to the user
    for question in questions:
        question_id = question.get("questionId")
        response = question.get("response")

        response = pepper + response + salt
        response = hashlib.sha256(response.encode("utf-8")).hexdigest().upper()
        tempo_core.user_questions.create(
            user_id=user.id,
            question_id=question_id,
            response=response
        )

    # Send the verification email
    try:
        handle_email(user_email=email, username=username, user_id=user.id)
    except (smtplib.SMTPException, KeyError) as e:
        return {"message": f"Erreur lors de l'envoi de l'email : {e.__class__.__name__}"}, 500

    return {"user": user.to_dict()}, 202


def check_password(password: str, username: str, email: str):
    """
    Password rules: (based on NIST recommendations (August 2024))

    - length: minimum 10 characters
    - no more than 3 identical characters in a row
    - not the name or derivatives of the name of the user
    - no series of numbers or letters longer than 3 characters
    - numbers, upper and lower case letters
    - Password not present in the list of compromised passwords (HIBP API)
    """
    print("IN CHECK PASSWORD")
    error_message = None
    status_code = 200

    # Checking password length
    if len(password) < 10:
        error_message = "Password length should be minimum 10."
        status_code = 400
        print("changed")

    # Checking for series or repetitions
    results = re.findall(r"(?=([a-z]{3}|[A-Z]{3}|\d{3}))", password)
    results_series = [
        match for match in results
        if (
            (ord(match[2]) - ord(match[1]) == 1)
            and (ord(match[1]) - ord(match[0]) == 1)
        )
    ]
    results_repetition = [
        match for match in results if match[0] == match[1] == match[2]
    ]
    if len(results_repetition) > 0:
        error_message = "You cannot have 3 identical characters in a row."
        status_code = 400
    if len(results_series) > 0:
        error_message = "Sequence longer than 3 characters detected."
        status_code = 400

    if not (
        any(letter.isdigit() for letter in password)
        and any(letter.isupper() for letter in password)
        and any(letter.islower() for letter in password)
    ):
        error_message = "Password must have a number, an uppercase letter, and a lowercase letter."
        status_code = 400

    # Checking if password contains user information
    for item in get_user_info(username, email):
        if item in password:
            error_message = "Password seems to contain personal information."
            status_code = 400

    # Call to HIBP API
    hashed_password = (
        hashlib.sha1(password.encode("utf-8"))
        .hexdigest()
        .upper()
    )
    hash_end = hashed_password[5:]
    hibp_client = HibpClient()
    response = hibp_client.check_breach(hashed_password[0:5])
    if not response:
        error_message = "Password checking feature is unavailable."
        status_code = 500
    for line in response:
        if line.split(":")[0] == hash_end:
            error_message = "Password is too weak."
            status_code = 400
    print("message : ", error_message)
    print("code : ", status_code)

    return ({"message": error_message}, status_code) if error_message else None


def generate_salt(length=5):
    """Generate a random salt."""
    return "".join(
        chr(random.randint(65, 90) if random.randint(0, 1) else random.randint(97, 122))
        for _ in range(length)
    )


def get_user_info(username: str, email: str):
    """
    Returns a set of potential user information
    :param username: username of the user
    :param email: email of the user
    :return: A set containing substring found with user information
    """

    email_first_part = email.split("@")[0].split(".")
    email_second_part = email.split("@")[1].split(".")[0]

    username_substring = generate_substrings(username)
    email_info_substring = []
    for info in email_first_part:
        email_info_substring += generate_substrings(info)

    checking_list = (
        username_substring
        + email_info_substring
        + [email_second_part]
    )
    return set(checking_list)


def generate_substrings(word):
    """
    Generate substrings from a word
    :param word: string we want the substrings of
    :return: substring with more than 4 letters of the word
    """

    return [word[0:j + 1].lower() for j in range(4 - 1, len(word))]
