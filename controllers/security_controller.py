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
from services.user import get_details
import re


def get_questions(**kwargs):
    """ Get the list of all questions """

    output = all_questions()

    return {"users": output}, 200


def get_question_by_id(**kwargs):
    """ Get question by id """

    id = kwargs.get("questionId")

    output = get_by_id(id)

    if not output:
        return {"message": f"Question with id {id} not found"}, 404

    return {"question": output}, 200


def get_question_by_question(**kwargs):
    """ Get question by question string """

    question = kwargs.get("question")

    output = get_by_question(question)

    if not output:
        return {"message": f"Question '{question}' not found"}, 404

    return {"question": output}, 200


def get_random_list(**kwargs):
    """ Get a random list of questions """

    number = kwargs.get("number")

    total = len(all_questions())
    if number > total:
        return {"message": "Length ask is above database length"}, 400

    output = get_random_questions(number)

    return {"question": output}, 200


def post_question(**kwargs):
    """ Create a list of questions """

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
    """ Delete a question """

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
