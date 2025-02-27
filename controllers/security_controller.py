from core.tempo_core import tempo_core


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
