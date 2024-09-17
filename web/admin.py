# web/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from mastermind.models import db, User, UserType
from mastermind.utils import generate_token, send_email, logger

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type.name != UserTypeEnum.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        user_type_name = request.form['user_type']
        user_type = UserType.query.filter_by(name=user_type_name).first()
        if not user_type:
            flash('Invalid user type.', 'danger')
            return redirect(url_for('admin.add_user'))

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists.', 'danger')
            return redirect(url_for('admin.add_user'))

        # Create new user with a temporary password
        temp_password = 'TemporaryPassword123'  # Consider generating a secure random password
        new_user = User(email=email, user_type=user_type)
        new_user.set_password(temp_password)
        db.session.add(new_user)
        db.session.commit()

        # Send welcome email
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

    user_types = UserType.query.all()
    return render_template('admin/add_user.html', user_types=user_types)

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    logger.info(f"User {user.email} deleted by admin {current_user.email}")
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.list_users'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type.name != UserTypeEnum.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
