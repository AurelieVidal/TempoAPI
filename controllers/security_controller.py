from services.question import (
    create,
    all_questions,
    get_by_id,
    get_random_questions,
    delete,
    get_by_question,
    get_by_question_id,
    delete_user_question
)
from services.user import get_details, get_by_username_phone
import re
from utils.utils import handle_email
from flask import request, render_template, session


def get_questions(**kwargs):
    """
    Get the list of all questions
    :param kwargs: unused
    :return: The list of all security questions
    """

    output = all_questions()

    return {"questions": output}, 200


def get_question_by_id(**kwargs):
    """
    Get question by id
    :param kwargs: A dict which contains the ID of the question
    :keyword questionId: The question ID
    :return: The corresponding question
    """

    id = kwargs.get("questionId")

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
    question_list = payload.get("questions")

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
    user = get_by_username_phone(username)
    if not user:
        return {"message": f"User with username {username} not found"}, 404
    email = user["email"]
    id = user["id"]

    token = session.get('email_token')
    if not token:
        # Resend the email depending on response types (json or HTML)
        if request.accept_mimetypes.accept_html:
            return (
                render_template('email_resend_template.html'),
                200,
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
        return {"message": "An error occurred while sending the email"}

    # Resend the email depending on response types (json or HTML)
    if request.accept_mimetypes.accept_html:
        return (
            render_template('email_resend_template.html'),
            200,
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
