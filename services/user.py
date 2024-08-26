from extensions import db
from models.user import User

def user_list():
    users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    return users
