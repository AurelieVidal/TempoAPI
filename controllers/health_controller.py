import os

from sqlalchemy.exc import SQLAlchemyError

from services.health import select_1
from utils.utils import call_to_api


def health_check(**kwargs):
    """
    Get the list of all users
    :param kwargs: unused
    :return: A message if the API and subj-ascents are working
    """

    # PSQL database
    try:
        select_1()
    except SQLAlchemyError:
        return {"error": "API is DEGRADED, database not accessible"}, 500

    # HIBP
    hipb_url = os.environ.get("HIPB_API_URL") + "00000"
    hipb_response = call_to_api(hipb_url)
    if not(hipb_response and hipb_response.status_code == 200):
        return {
            "error": "API is DEGRADED, subj-ascent HIBP not accessible"
        }, 500

    return {"users": "API is UP"}, 200
