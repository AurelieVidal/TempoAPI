import hashlib
import json
import os
import random
from datetime import datetime, timedelta

from core.models import StatusEnum
from core.models.connection import Connection, ConnectionStatusEnum
from core.tempo_core import tempo_core
from utils.utils import handle_email_forgotten_password


def get_questions(**kwargs):
    """
    GET /security/questions
    :return: The list of all security questions
    """

    questions = tempo_core.question.get_all()
    output = [question.to_dict() for question in questions]

    return {"questions": output}, 200


def get_question_by_id(**kwargs):
    """
    GET /security/question/{questionId}

    Params :
        - questionId in kwargs, to filter questions by id
    :return: The question
    """
    question_id = kwargs.get("questionId")
    question = tempo_core.question.get_by_id(question_id)

    if not question:
        return {"message": f"Question with id {question_id} not found"}, 404

    return {"question": question.to_dict()}, 200


def get_random_list(**kwargs):
    """
    GET /security/question/random/{number}

    Params :
        - number in kwargs, the desired number of questions
    :return: The list of random questions
    """
    number = kwargs.get("number")

    total = len(tempo_core.question.get_all())

    if number > total:
        return {"message": "Length ask is above database length"}, 400

    output = tempo_core.question.get_random_questions(number)

    return {"questions": output}, 200


def check_user():
    """
    GET /security/check-user
    """
    return {"message": "User successfully authenticated"}, 200


def validate_connection(**kwargs):
    """
    POST /security/validate-connection/{username}
    """

    conn_id = kwargs.get("validationId")
    username = kwargs.get("username")
    answer = kwargs.get("answer")

    # Validate connection
    conn = get_connection(conn_id)
    if not conn:
        return {"message": "validationId is not valid"}, 404

    if datetime.now() - conn.date > timedelta(minutes=5):
        return {"message": "validationId is expired"}, 404

    # Validate the user
    user, response_body, status_code = check_user_status(username)
    if response_body:
        return response_body, status_code

    # Validate the answer
    conn_output = json.loads(conn.output)
    question = conn_output.get("question")
    user_questions = [qu for qu in user.questions if qu.question.question == question]

    if not user_questions:
        return {"message": "Unexpected error"}, 500

    user_question = user_questions[0]

    response = os.environ.get("PEPPER") + answer + user.salt
    response = hashlib.sha256(response.encode("utf-8")).hexdigest().upper()

    if response != user_question.response:
        # Create a new connection

        tempo_core.connection.create(
            user_id=user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.VALIDATION_FAILED,
        )

        # Check try number
        failed_connections = tempo_core.connection.get_list_by_key(
            order_by=Connection.date,
            limit=3,
            order="desc",
            user_id=user.id
        )

        max_failed = False
        if len(failed_connections) >= 3:
            max_failed = all(
                connection.status == ConnectionStatusEnum.VALIDATION_FAILED
                for connection in failed_connections
            )

        if max_failed:
            tempo_core.user.update(user.id, status=StatusEnum.BANNED)
            response_body = {
                "message": f"Reached max number of tries, user {username} is now banned. "
                           "To reactivate the account please contact "
                           "admin support at t26159970@gmail.com"
            }
            status_code = 403
        else:
            response_body = {"message": "Provided answer does not match"}
            status_code = 403

        return response_body, status_code

    # Forgotten password process also uses this process, thus we use sepcial enums
    if conn.status == ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD:
        tempo_core.connection.update(conn.id, status=ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD)
    else:
        tempo_core.connection.update(conn.id, status=ConnectionStatusEnum.VALIDATED)

    return {"message": "Connection has been validated, you can try to authenticate again."}, 200


def get_connection(conn_id):
    conn_sus = tempo_core.connection.get_list_by_key(
        order_by=Connection.date,
        limit=1,
        order="desc",
        id=conn_id,
        status=ConnectionStatusEnum.SUSPICIOUS
    )

    conn_forgot = tempo_core.connection.get_list_by_key(
        order_by=Connection.date,
        limit=1,
        order="desc",
        id=conn_id,
        status=ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD
    )

    if conn_sus:
        return conn_sus[0]
    if conn_forgot:
        return conn_forgot[0]


def check_user_status(username):
    user = tempo_core.user.get_instance_by_key(username=username)
    if not user:
        return None, {"message": f"User {username} not found"}, 404
    if user.status == StatusEnum.BANNED:
        return None, {"message": f"User {username} is banned"}, 401
    return user, None, None


def forgotten_password(**kwargs):
    """
    GET /security/forgotten-password
    """

    username = kwargs.get("username")
    user = tempo_core.user.get_instance_by_key(username=username)

    if not user:
        return {"message": f"User {username} not found"}, 404

    last_conn_list = tempo_core.connection.get_list_by_key(
        order_by=Connection.date,
        limit=1,
        order="desc",
        user_id=user.id
    )

    # Check if a connection has been validated or not
    if not last_conn_list:
        create_conn = True
    else:
        last_conn = last_conn_list[0]
        if (
                last_conn.status == ConnectionStatusEnum.ALLOW_FORGOTTEN_PASSWORD
                and datetime.now() - last_conn.date < timedelta(minutes=5)
        ):
            create_conn = False
        else:
            create_conn = True

    if create_conn:
        # Create the connection and return the question
        user_question = random.choice(user.questions)
        msg = {
            "message": "You need to validate connection by answering a security question",
            "question": user_question.question.question
        }
        connection = tempo_core.connection.create(
            user_id=user.id,
            date=datetime.now(),
            status=ConnectionStatusEnum.ASK_FORGOTTEN_PASSWORD,
            output=json.dumps(msg, ensure_ascii=False)
        )

        msg["validation_id"] = connection.id
        return msg, 401

    # Everything OK, send the email to resend the connection
    handle_email_forgotten_password(user)
    return {"message": "Demand validated, an email has been sent to the user"}, 200
