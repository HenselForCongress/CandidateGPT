# mastermind/utils/auth.py
from functools import wraps
from flask import abort
from flask_login import current_user
from mastermind.models import UserTypeEnum
from .logging import logger

def role_required(*roles):
    """Decorator to restrict access to specific roles"""
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                logger.warning(f"403 Forbidden: User not authenticated")
                abort(403)

            logger.debug(f"Current user email: {current_user.email}")
            logger.debug(f"Current user type: {current_user.user_type.name.value}")

            if current_user.user_type.name.value not in roles:
                logger.warning(f"403 Forbidden: User {current_user.email} does not have the required role {roles}")
                abort(403)

            logger.info(f"User {current_user.email} has access with role {current_user.user_type.name.value}")
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
