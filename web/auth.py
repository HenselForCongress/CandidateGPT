# web/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from mastermind.models import db, User, UserType, UserTypeEnum
from mastermind.utils.email import send_email
from mastermind.utils.token_utils import generate_token, confirm_token
from mastermind.utils.logging import logger
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Loading user with id: {user_id}")
    return User.query.get(user_id)

# Initialize Flask-Limiter
limiter = Limiter(key_func=get_remote_address)

# Password strength validation function
def is_strong_password(password):
    logger.debug("Validating password strength.")
    # Password must be at least 42 characters long, contain uppercase, lowercase, digit, and special character
    if (len(password) < 42 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        logger.warning("Weak password attempted.")
        return False
    return True

# Flask-WTF Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class SetupAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    user_count = User.query.count()
    logger.debug(f"Number of users in the system: {user_count}")
    if user_count == 0:
        flash('No users found. Please create an admin account.', 'info')
        logger.info("No users found in the system. Redirecting to setup admin.")
        return redirect(url_for('auth.setup_admin'))

    if current_user.is_authenticated:
        logger.info(f"User {current_user.email} is already authenticated. Redirecting to main page.")
        return redirect(url_for('web_bp.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        logger.debug(f"Login attempt with email: {email}")

        # Check for is_active directly
        user = User.query.filter_by(email=email).first()
        if user and user.is_active and user.check_password(password):
            login_user(user)
            logger.info(f"User {user.email} logged in from IP {request.remote_addr}.")
            flash('Logged in successfully!', 'success')
            return redirect(url_for('web_bp.index'))
        else:
            logger.warning(f"Failed login attempt for email: {email} from IP {request.remote_addr}")
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)

# Setup Admin route

@auth_bp.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    logger.debug("Accessed setup_admin route.")
    # Check if users already exist
    user_count = User.query.count()
    logger.debug(f"User count: {user_count}")
    if user_count > 0:
        flash('Admin account already exists. Please log in.', 'info')
        logger.info("Admin account already exists. Redirecting to login.")
        return redirect(url_for('auth.login'))

    form = SetupAdminForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        logger.debug(f"Form submitted with email: {email}")

        if not is_strong_password(password):
            flash('Password must be at least 42 characters long and include uppercase, lowercase, number, and special character.', 'danger')
            logger.warning("Password did not meet strength requirements.")
            return render_template('auth/setup_admin.html', form=form)

        # Create an admin user
        admin_type = UserType.query.filter_by(name=UserTypeEnum.ADMIN).first()
        if not admin_type:
            logger.debug("Admin UserType not found. Creating new one.")
            # Create admin user type if it doesn't exist
            admin_type = UserType(name=UserTypeEnum.ADMIN)
            db.session.add(admin_type)
            db.session.commit()

        new_user = User(email=email, user_type=admin_type)
        new_user.set_password(password)
        db.session.add(new_user)
        try:
            db.session.commit()
            login_user(new_user)
            logger.info(f"Admin user {new_user.email} created from IP {request.remote_addr}.")
            flash('Admin account created successfully!', 'success')
            return redirect(url_for('web_bp.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating admin user: {e}")
            flash('An error occurred while creating the admin account.', 'danger')
            return render_template('auth/setup_admin.html', form=form)
    else:
        if form.errors:
            logger.debug(f"Form validation errors: {form.errors}")

    return render_template('auth/setup_admin.html', form=form)

# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logger.info(f"User {current_user.email} logged out from IP {request.remote_addr}.")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# Password Reset Request Route
@auth_bp.route('/password-reset', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def password_reset_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token(user.email, salt='password-reset')
            send_email(
                subject='Reset Your Password',
                recipient=user.email,
                template='email/password_reset.html',
                token=token
            )
            logger.info(f"Password reset email sent to {user.email} from IP {request.remote_addr}.")
        else:
            logger.warning(f"Password reset requested for non-existent email: {email} from IP {request.remote_addr}.")
        flash('If your email is registered, you will receive a password reset link.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset_request.html', form=form)

# Password Reset Route
@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = confirm_token(token, salt='password-reset')
    if not email:
        logger.error("💔 Invalid or expired password reset link.")
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.password_reset_request'))

    user = User.query.filter_by(email=email).first_or_404()

    form = ResetPasswordForm()
    if form.validate_on_submit():
        password = form.password.data

        if not is_strong_password(password):
            logger.warning(f"Weak password attempt during reset for user {email}.")
            flash('Password must be at least 42 characters long and include uppercase, lowercase, number, and special character.', 'danger')
            return render_template('auth/reset_password.html', form=form)

        user.set_password(password)
        db.session.commit()
        logger.info(f"Password updated for user {user.email} from IP {request.remote_addr}.")
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            email = form.email.data
            user_type = UserType.query.filter_by(name=UserTypeEnum.VIEWER).first()
            new_user = User(email=email, user_type=user_type)
            db.session.add(new_user)
            db.session.commit()

            # Send a password reset email
            token = generate_token(new_user.email, salt='password-reset')
            send_email(
                subject='Welcome to CandidateGPT - Set Your Password',
                recipient=new_user.email,
                template='email/welcome_with_reset.html',
                token=token
            )
            flash('Registration successful. Please check your email to set your password.', 'success')
            logger.info(f"New viewer account {email} registered.")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during registration for {email}: {e}")
            flash('An error occurred during registration.', 'danger')
    return render_template('auth/register.html', form=form)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        given_name = request.form.get('given_name')
        family_name = request.form.get('family_name')
        preferred_name = request.form.get('preferred_name')
        organization_name = request.form.get('organization')
        notes = request.form.get('notes')

        # Update user profile
        current_user.given_name = given_name
        current_user.family_name = family_name
        current_user.preferred_name = preferred_name
        current_user.notes = notes

        # Handle organization creation if needed
        if organization_name:
            organization = Organization.query.filter_by(name=organization_name).first()
            if not organization:
                # Create a new organization
                organization = Organization(name=organization_name)
                db.session.add(organization)
                db.session.flush()  # Flush to get the new organization ID

            current_user.organization_id = organization.id

        try:
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile.', 'danger')

    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/security', methods=['GET', 'POST'])
@login_required
def security():
    if request.method == 'POST':
        # Placeholder for future security settings (e.g., 2FA)
        pass
    return render_template('auth/security.html', user=current_user)

