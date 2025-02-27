from sqlalchemy.exc import SQLAlchemyError

from adapters.hibp_client import HibpClient
from core.tempo_core import tempo_core


def health_check():
    """
    GET /health
    :return: A message if the API and subj-ascents are working
    """

    # PSQL database
    try:
        tempo_core.health.select_1()
    except SQLAlchemyError:
        return {"error": "API is DEGRADED, database not accessible"}, 500

    # HIBP
    hibp_client = HibpClient()
    try:
        hibp_client.check_breach("00000")
    except RuntimeError:
        return {"error": "API is DEGRADED, subj-ascent HIBP not accessible"}, 500

    return {"message": "API is UP"}, 200
