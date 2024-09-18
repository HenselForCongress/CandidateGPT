# mastermind/models.py
from datetime import datetime
from flask import request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import enum
from sqlalchemy import (func, Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Index)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow import Schema, fields, validate
from flask_login import UserMixin
from .utils import logger

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy()
migrate = Migrate()

def generate_uuid():
    """Generate a unique UUID."""
    uuid_generated = str(uuid.uuid4())
    logger.debug(f"Generated UUID: {uuid_generated}")
    return uuid_generated

class UserTypeEnum(enum.Enum):
    ADMIN = "Admin"
    USER = "User"
    VIEWER = "Viewer"

class UserType(db.Model):
    """UserType model to define different user roles such as admin, user, viewer."""
    __tablename__ = 'user_types'
    __table_args__ = {'schema': 'meta'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    name = db.Column(db.Enum(UserTypeEnum), unique=True, nullable=False, comment="Name of the user type (e.g., Admin, User, Viewer)")
    description = db.Column(db.String(255), nullable=True, comment="Description of the user type")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record last update date")

    def __repr__(self):
        return f"<UserType {self.name}>"

class UserSchema(Schema):
    user_id = fields.UUID()
    email = fields.Email(required=True)
    is_active = fields.Boolean()
    user_type = fields.String(validate=validate.OneOf([e.value for e in UserTypeEnum]))
    last_login = fields.DateTime()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class User(db.Model, UserMixin):
    """User model for storing user details and credentials."""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'entities'}

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid, comment="Unique user ID")
    email = db.Column(db.String(255), unique=True, nullable=False, comment="User's email address", index=True)
    password_hash = db.Column(db.Text, nullable=False, comment="Hashed password")
    is_active = db.Column(db.Boolean, default=True, nullable=False, comment="Is the user active?")
    user_type_id = db.Column(db.Integer, db.ForeignKey('meta.user_types.id', ondelete='CASCADE'), nullable=False, comment="Foreign key to the user type")
    last_login = db.Column(db.DateTime, nullable=True, comment="Last login time")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record last update date")
    queries = db.relationship('Query', backref='user', lazy=True, cascade="all, delete-orphan")
    user_type = db.relationship('UserType', backref='users')

    def set_password(self, password):
        """Hash and set the user's password."""
        logger.debug(f"Setting password for user {self.email}")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        logger.debug(f"Checking password for user {self.email}")
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Return the user's unique ID as a string."""
        return str(self.user_id)

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        logger.debug(f"Checking if user {self.email} is authenticated")
        return True

    @property
    def is_anonymous(self):
        """Return False, as this is not an anonymous user."""
        return False

    def serialize(self):
        """Serialize the User object to a dictionary."""
        logger.debug(f"Serializing user {self.email}")
        return UserSchema().dump(self)

    def __repr__(self):
        return f"<User {self.email}>"

# Add an index on email
Index('idx_users_email', User.email)

class QuerySchema(Schema):
    id = fields.Integer()
    query_text = fields.String(required=True)
    response_text = fields.String(required=True)
    settings_selected = fields.String()
    timestamp = fields.DateTime()
    ip_address = fields.String(validate=validate.Length(max=45))
    user_id = fields.UUID()  # Foreign key to User
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class Query(db.Model):
    """Query model for storing user queries and their responses."""
    __tablename__ = 'queries'
    __table_args__ = {'schema': 'logs'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    query_text = db.Column(db.Text, nullable=False, comment="Text of the query made by the user")
    response_text = db.Column(db.Text, nullable=False, comment="Response text for the query")
    settings_selected = db.Column(db.String(255), nullable=True, comment="Settings used when making the query")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment="Time when query was made")
    ip_address = db.Column(db.String(45), nullable=True, comment="IP address from which the query was made")
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entities.users.user_id', ondelete='CASCADE'), nullable=False, comment="ID of the user who made the query")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record last update date")

    def __init__(self, query_text, response_text, settings_selected, user_id):
        self.query_text = query_text
        self.response_text = response_text
        self.settings_selected = settings_selected
        self.user_id = user_id
        self.ip_address = request.remote_addr  # Capture the IP address
        logger.debug(f"New Query created: {self.serialize()}")

    def serialize(self):
        """Serialize the Query object to a dictionary."""
        logger.debug(f"Serializing query {self.id}")
        return QuerySchema().dump(self)

    def __repr__(self):
        return f"<Query {self.id} by User {self.user_id}>"

class ResponseSchema(Schema):
    id = fields.Integer()
    response_text = fields.String(required=True)
    query_id = fields.Integer()  # Foreign key to Query
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class Response(db.Model):
    """Response model for storing responses separately if needed."""
    __tablename__ = 'responses'
    __table_args__ = {'schema': 'logs'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    response_text = db.Column(db.Text, nullable=False, comment="Response text")
    query_id = db.Column(db.Integer, db.ForeignKey('logs.queries.id', ondelete='CASCADE'), nullable=False, comment="Associated query ID")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record last update date")

    def serialize(self):
        """Serialize the Response object to a dictionary."""
        logger.debug(f"Serializing response {self.id}")
        return ResponseSchema().dump(self)

    def __repr__(self):
        return f"<Response {self.id} for Query {self.query_id}>"

class ActivitySchema(Schema):
    id = fields.Integer()
    activity_type = fields.String(required=True)
    description = fields.String(required=True)
    user_id = fields.UUID()  # Foreign key to User
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class Activity(db.Model):
    """Activity model for logging user activities such as login attempts, failures, updates."""
    __tablename__ = 'activity'
    __table_args__ = {'schema': 'logs'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    activity_type = db.Column(db.String(50), nullable=False, comment="Type of activity (e.g., login, update)")
    description = db.Column(db.Text, nullable=False, comment="Detailed description of the activity")
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entities.users.user_id', ondelete='CASCADE'), nullable=False, comment="ID of the user who performed the activity")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, server_default=func.now(), nullable=False, comment="Record last update date")

    def serialize(self):
        """Serialize the Activity object to a dictionary."""
        logger.debug(f"Serializing activity {self.id}")
        return ActivitySchema().dump(self)

    def __repr__(self):
        return f"<Activity {self.id} by User {self.user_id}>"
