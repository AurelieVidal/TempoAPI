from services.user import (
    user_list,
    create,
    get_by_username,
    get_details,
    add_question_to_user,
    update
)
from services.question import get_by_id
from models.user import StatusEnum
import random
import re
import hashlib
import os
import requests
from retry import retry


def get_users(**kwargs):
    """ Get the list of all users """

    output = user_list()

    return {"users": output}, 200


def get_user_by_username(**kwargs):
    """ Retrieve a user by username """

    username = kwargs.get("username")

    output = get_by_username(username)

    return {"users": output}, 200


def get_user_details(**kwargs):
    """ Get details of a user """

    id = kwargs.get("userId")

    output = get_details(id)
    if not output:
        return {"message": f"User {id} not found or incomplete"}, 400

    return {"users": output}, 200


def patch_user(**kwargs):
    """ Update a a user """

    id = kwargs.get("userId")
    payload = kwargs.get("body")
    status = payload.get("status")

    if not status:
        user = get_details(id)
        output = {
            "id": id,
            "username": user.get("username"),
            "email": user.get("email")
        }
        return {"users": output}, 200

    output = update(id, StatusEnum.READY.value)
    if not output:
        return {"message": f"User {id} not found"}, 404

    return {"users": output}, 200


def post_users(**kwargs):
    """ Create a user """

    payload = kwargs.get("body")
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    questions = payload.get("questions")
    device = payload.get("device")

    # Check if questions exists
    for question in questions:
        question_id = question.get("questionId")
        if not get_by_id(question_id):
            return {"message": f"Question {question_id} not found"}, 400

    # Check username
    if get_by_username(username):
        return {"message": "Username is already used"}, 400

    """
    Password rules: (based on NIST recommendations (August 2024))
    - length: minimum 10 characters
    - no more than 3 identical characters in a row
    - not the name or derivatives of the name of the user
    - no series of numbers or letters longer than 3 characters
    - numbers, upper and lower case letters
    - Password not present in the list of compromised passwords (HIBP API)
    """

    # Checking for series or repetitions
    pattern = r"(?=([a-z]{3}|[A-Z]{3}|\d{3}))"
    results = re.findall(pattern, password)
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
        return {
            "message": "You cannot have 3 identical characters in a row."
        }, 400
    if len(results_series) > 0:
        return {
            "message": "Sequence longer than 3 characters detected."
        }, 400

    has_number = any(letter.isdigit() for letter in password)
    has_upper = any(letter.isupper() for letter in password)
    has_lower = any(letter.islower() for letter in password)
    if not (has_number and has_upper and has_lower):
        return {
            "message": (
                "Password must have a number, an uppercase letter, "
                "and a lowercase letter."
            )
        }, 400

    # Checking is password contains user information
    checking_list = get_user_info(username, email)
    for item in checking_list:
        if item in password:
            return {
                "message": "Password seems to contain personal information."
            }, 400

    # Call to HIBP API
    hashed_password = (
        hashlib.sha1(password.encode("utf-8"))
        .hexdigest()
        .upper()
    )
    hash_beginning = hashed_password[0:5]
    hash_end = hashed_password[5:]
    hipb_url = os.environ.get("HIPB_API_URL") + hash_beginning

    response = call_to_api(hipb_url)
    if not response:
        return {
            "message": "Password checking feature is unavailable."
        }, 500
    response = response.text.splitlines()
    for line in response:
        if line.split(":")[0] == hash_end:
            return {"message": "Password is too weak."}, 400

    # Creating the salt (specific for the user)
    salt = ""
    for _ in range(5):
        random_integer = random.randint(97, 97 + 26 - 1)
        is_capital = random.randint(0, 1)
        random_integer = random_integer - 32 \
            if is_capital == 1 else random_integer
        salt += chr(random_integer)

    # Hash the password
    pepper = os.environ.get("PEPPER")
    password = pepper + password + salt
    password = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()

    # Create the user
    output = create(
        username=username,
        email=email,
        password=password,
        salt=salt,
        device=device
    )

    user_id = output.get("id")
    for question in questions:
        question_id = question.get("questionId")
        response = question.get("response")

        response = pepper + response + salt
        response = hashlib.sha256(response.encode("utf-8")).hexdigest().upper()
        add_question_to_user(
            user_id=user_id,
            question_id=question_id,
            response=response
        )

    return {"users": output}, 202


def get_user_info(username, email):
    """ Returns a set of potential user information. """

    email_first_part = email.split('@')[0].split('.')
    email_second_part = email.split('@')[1].split('.')[0]

    username_substring = generate_substrings(username)
    email_info_substring = []
    for info in email_first_part:
        email_info_substring += generate_substrings(info)

    checking_list = (
        username_substring +
        email_info_substring +
        [email_second_part]
    )
    return set(checking_list)


def generate_substrings(word):
    """ Generate substrings of a word. """

    return [word[0:j+1].lower() for j in range(4 - 1, len(word))]


@retry(requests.RequestException, tries=5, delay=2)
def call_to_api(url):
    """ Call to API """

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return
    return response
