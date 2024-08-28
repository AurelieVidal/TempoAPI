from app import db
from .user import User

# Exposez le metadata des modèles via `Base`
Base = db.Model