from app import db

from .question import Question  # noqa: F401
from .user import User  # noqa: F401
from .user_question import UserQuestion  # noqa: F401

Base = db.Model
