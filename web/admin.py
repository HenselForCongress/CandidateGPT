# web/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from mastermind.models import db, User, UserType, UserTypeEnum
from mastermind.utils import generate_token, send_email, logger

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning("Unauthorized access attempt. User not authenticated.")
            abort(403)
        if current_user.user_type.name != UserTypeEnum.ADMIN.value:
            logger.error(f"Access denied for user {current_user.email}. Not an admin.")
            abort(403)
        logger.info(f"Admin access granted to user {current_user.email}.")
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    try:
        users = User.query.all()
        logger.info("User list retrieved successfully.")
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        flash('An error occurred while retrieving users.', 'danger')
        abort(500)


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        user_type_name = request.form['user_type']
        logger.debug(f"Attempting to add user with email: {email} and user_type: {user_type_name}")

        user_type = UserType.query.filter_by(name=user_type_name).first()
        if not user_type:
            logger.warning(f"Invalid user type specified: {user_type_name}")
            flash('Invalid user type.', 'danger')
            return redirect(url_for('admin.add_user'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            logger.warning(f"User with email {email} already exists.")
            flash('User with this email already exists.', 'danger')
            return redirect(url_for('admin.add_user'))

        try:
            temp_password = 'TemporaryPassword123'  # Consider generating a secure random password
            new_user = User(email=email, user_type=user_type)
            new_user.set_password(temp_password)
            db.session.add(new_user)
            db.session.commit()

            send_email(
                subject='Welcome to CandidateGPT',
                recipient=new_user.email,
                template='email/welcome.html',
                user=new_user,
                temp_password=temp_password
            )
            logger.info(f"New user {new_user.email} added by admin {current_user.email}")
            flash('User added successfully.', 'success')
            return redirect(url_for('admin.list_users'))

        except Exception as e:
            logger.error(f"Error adding new user {email}: {e}")
            db.session.rollback()
            flash('An error occurred while adding the user.', 'danger')
            return redirect(url_for('admin.add_user'))

    user_types = UserType.query.all()
    logger.debug("Retrieving user types for add user form.")
    return render_template('admin/add_user.html', user_types=user_types)


@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        logger.info(f"User {user.email} deleted by admin {current_user.email}")
        flash('User deleted successfully.', 'success')
        return redirect(url_for('admin.list_users'))
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        flash('An error occurred while deleting the user.', 'danger')
        return redirect(url_for('admin.list_users'))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type.name != UserTypeEnum.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
