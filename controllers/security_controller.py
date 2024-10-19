import re

from flask import render_template, request, session

from services.question import (all_questions, create, delete,
                               delete_user_question, get_by_id,
                               get_by_question, get_by_question_id,
                               get_random_questions)
from services.user import get_by_username, get_details
from utils.utils import handle_email


def get_questions(**kwargs):
    """
    Get the list of all questions
    :param kwargs: unused
    :return: The list of all security questions
    """

    output = all_questions()
    if not output:
        output = []

    return {"questions": output}, 200


def get_question_by_id(**kwargs):
    """
    Get question by id
    :param kwargs: A dict which contains the ID of the question
    :keyword questionId: The question ID
    :return: The corresponding question
    """

    id = kwargs.get("questionId")
    if not id or not isinstance(id, int):
        return {"message": "Input error, questionId is not defined"}, 400

    output = get_by_id(id)

    if not output:
        return {"message": f"Question with id {id} not found"}, 404

    return {"question": output}, 200


def get_question_by_question(**kwargs):
    """
    Get question by question string
    :param kwargs: A dict which contains the question
    :keyword question: The question
    :return: The corresponding question
    """

    question = kwargs.get("question")
    if not question:
        return {"message": "Input error, question is not defined"}, 400

    output = get_by_question(question)

    if not output:
        return {"message": f"Question '{question}' not found"}, 404

    return {"question": output}, 200


def get_random_list(**kwargs):
    """
    Get a random list of n questions, n is given by the user
    :param kwargs: A dict which contains the number parameter
    :keyword number: the desired number of questions
    :return: The list of random questions
    """

    number = kwargs.get("number")
    if not number:
        return {"message": "Input error, number is not defined"}, 400

    total = len(all_questions())
    if number > total:
        return {"message": "Length ask is above database length"}, 400

    output = get_random_questions(number)

    return {"questions": output}, 200


def post_question(**kwargs):
    """
    Create questions
    :param kwargs: A dict which contains the questions to create
    :keyword body.questions: The list of questions
    :return: A list of the created questions
    """

    payload = kwargs.get("body")
    if not payload:
        return {"message": "Input error, body is not defined"}, 400

    question_list = payload.get("questions")
    if not question_list:
        return {"message": "Input error, questions is not defined"}, 400

    pattern = r'^[A-Z].*\?$'
    format_question = all(
        re.match(pattern, question) for question in question_list
    )
    if not format_question:
        return {
            "message": "One of the question does not have the good format."
        }, 400

    created_questions = []
    for question in question_list:
        if not get_by_question(question):
            new_question = create(question)
            created_questions.append(new_question)
        else:
            return {"message": f"Question '{question}' already exist"}, 400

    return {"questions": created_questions}, 200


def delete_question(**kwargs):
    """
    Delete a question
    :param kwargs: A dict which contains the question ID
    :keyword questionId: ID of the question to delete
    :return: The deleted question
    """

    id = kwargs.get("questionId")
    if not id or not isinstance(id, int):
        return {"message": "Input error, body is not defined"}, 400

    users = get_by_question_id(id)
    for user in users:
        user = get_details(user)
        question_list = user.get("questions")
        if len(question_list) == 1:
            return {
                "message": "One or more users is only related to this question"
            }, 400

    delete_user_question(id)

    output = delete(id)
    if not output:
        return {"message": f"Question with id {id} not found"}, 404

    return {"question": output}, 200


def resend_email(**kwargs):
    """
    Resend a verification email
    :param kwargs: A dict which contains the user to send the mail
    :keyword username: Username of the user which need a new mail
    :return: Success message or success template
    """

    username = kwargs.get("username")
    if not username:
        return {"message": "Input error, username is not defined"}, 400

    user = get_by_username(username)
    if not user:
        return {"message": f"User with username {username} not found"}, 404
    user = get_details(user["id"])
    user = {
        "id": user["id"],
        "username": user["username"],
        "phone": user["phone"],
        "email": user["email"]
    }
    email = user.get("email")
    id = user.get("id")

    token = session.get('email_token')
    if not token:
        # Resend the email depending on response types (json or HTML)
        if request.accept_mimetypes.accept_html:
            return (
                render_template('email_resend_template.html'),
                202,
                conforming_response_header()
            )

        return (
            {"message": "Email has been resend with success"},
            202,
            conforming_response_header()
        )

    session.pop('email_token', None)

    try:
        handle_email(user_email=email, username=username, user_id=id)
    except Exception:
        return {"message": "An error occurred while sending the email"}, 500

    # Resend the email depending on response types (json or HTML)
    if request.accept_mimetypes.accept_html:
        return (
            render_template('email_resend_template.html'),
            202,
            conforming_response_header()
        )

    return (
        {"message": "Email has been resend with success"},
        202,
        conforming_response_header()
    )


def conforming_response_header():
    """
    Check for the appropriate format of response
    :return: Content-Type header of the response
    """
    if request.accept_mimetypes.accept_html:
        return {'Content-Type': 'text/html'}
    return {'Content-Type': 'application/json'}
