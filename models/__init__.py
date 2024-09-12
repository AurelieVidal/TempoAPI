from app import db
from .user import User  # noqa: F401
from .question import Question  # noqa: F401
from .user_question import UserQuestion  # noqa: F401


Base = db.Model
