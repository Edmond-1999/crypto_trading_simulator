
from werkzeug.security import check_password_hash

from app.models import User


def authenticate_user(email: str, password: str):
    user = User.query.filter_by(email=email.strip().lower()).first()

    if user is None:
        return None

    if not check_password_hash(user.password_hash, password):
        return None

    return user
