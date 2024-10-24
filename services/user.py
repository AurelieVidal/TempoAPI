import json

from models.question import Question
from models.user import StatusEnum, User
from models.user_question import UserQuestion

from . import session_scope


def user_list():
    """
    Get the list of all users
    :return: The list of all users
    """

    with session_scope() as session:
        query = session.query(User).filter(User.status == StatusEnum.READY)

        output = []
        for item in query.all():
            output.append(
                {
                    "id": item.id,
                    "username": item.username,
                    "email": item.email
                }
            )

        return output


def get_by_username(username):
    """
    Get user by username
    :param username: The username we search
    :return: The corresponding user
    """

    with session_scope() as session:
        query = session.query(User)
        query = query.filter(User.username == username)
        user = query.first()
        if not user:
            return

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }


def get_details(id: int):
    """
    Get details about a user
    :param id: ID of the user
    :return: A dict with all information about the user
    """

    with session_scope() as session:
        query = (
            session.query(
                User.id,
                User.username,
                User.email,
                User.devices,
                User.status,
                User.phone,
                Question.question,
                Question.id.label("question_id")
            )
            .join(UserQuestion, UserQuestion.user_id == User.id)
            .join(Question, UserQuestion.question_id == Question.id)
        )
        query = query.filter(User.id == id)
        user = query.first()

        if not user:
            return

        questions = []
        for item in query.all():
            questions.append({
                "question": item.question,
                "id": item.question_id
            })

        devices = json.loads(user.devices)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "questions": questions,
            "devices": devices,
            "status": user.status.value,
            "phone": user.phone,
        }


def create(
        username: str,
        email: str,
        password: str,
        salt: str,
        device: str,
        phone: str
):
    """
    Create a user
    :param username: Username chosen by the user
    :param email: Email of the user
    :param password: Password of the user
    :param salt: Generated char sequence associated to the user
    :param device: Detected device of the user
    :param phone: Phone number of the user (should be international format)
    :return: The created user
    """

    with session_scope() as session:
        new_user = User(
            username=username,
            email=email,
            password=password,
            salt=salt,
            devices=f'["{device}"]',
            status=StatusEnum.CHECKING_EMAIL,
            phone=phone
        )
        session.add(new_user)
        session.commit()

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }


def update(
        id: int,
        status: str
):
    """
    Update a user
    :param id: ID of the user
    :param status: new status of the user
    :return: The updated user
    """

    with session_scope() as session:
        (
            session.query(User)
            .filter(User.id == id)
            .update({'status': status})
        )
        session.commit()

        user = session.query(User).filter(User.id == id).first()
        if not user:
            return

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }


def add_question_to_user(user_id: int, question_id: int, response: str):
    """
    Associate a question to a user
    :param user_id: ID of the user
    :param question_id: ID of the question
    :param response: answer of the user to the question
    :return: associate the question to the user
    """
    """ Associate a question to a user """

    with session_scope() as session:
        new_user = UserQuestion(
            user_id=user_id,
            question_id=question_id,
            response=response
        )
        session.add(new_user)
        session.commit()


def get_security_infos(user_id: int):
    """
    Get details about a user
    :param user_id: ID of the user
    :return: A dict with all information about the user
    """
    with session_scope() as session:
        query = (
            session.query(
                User.salt,
                User.password
            )
        )
        query = query.filter(User.id == user_id)
        user = query.first()

        if not user:
            return

        return {
            "salt": user.salt,
            "password": user.password
        }
