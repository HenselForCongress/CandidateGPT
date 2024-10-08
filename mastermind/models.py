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
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"

class UserType(db.Model):
    """UserType model to define different user roles such as admin, user, viewer."""
    __tablename__ = 'user_types'
    __table_args__ = {'schema': 'meta'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    name = db.Column(db.Enum(UserTypeEnum), unique=True, nullable=False, comment="Name of the user type (e.g., Admin, User, Viewer)")
    description = db.Column(db.String(255), nullable=True, comment="Description of the user type")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Record last update date")

    def __repr__(self):
        return f"<UserType {self.name}>"

class Organization(db.Model):
    """Organization model for storing organization details."""
    __tablename__ = 'organizations'
    __table_args__ = {'schema': 'entities'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    name = db.Column(db.String(255), unique=True, nullable=False, comment="Name of the organization")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Record last update date")

    def __repr__(self):
        return f"<Organization {self.name}>"

class UserSchema(Schema):
    user_id = fields.UUID()
    email = fields.Email(required=True)
    is_active = fields.Boolean()
    given_name = fields.String()
    family_name = fields.String()
    preferred_name = fields.String()
    organization = fields.String()
    notes = fields.String()
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
    given_name = db.Column(db.String(255), nullable=True, comment="User's given name")
    family_name = db.Column(db.String(255), nullable=True, comment="User's family name (if applicable)")
    preferred_name = db.Column(db.String(255), nullable=True, comment="User's preferred name")
    notes = db.Column(db.Text, nullable=True, comment="Notes about the user, including how they plan to use the tool")
    organization_id = db.Column(db.Integer, db.ForeignKey('entities.organizations.id', ondelete='SET NULL'), nullable=True, comment="Foreign key to the organization")
    user_type_id = db.Column(db.Integer, db.ForeignKey('meta.user_types.id', ondelete='CASCADE'), nullable=False, comment="Foreign key to the user type")
    last_login = db.Column(db.DateTime, nullable=True, comment="Last login time")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Record last update date")

    organization = db.relationship('Organization', backref='users', lazy='joined')
    queries = db.relationship('Query', backref='user', lazy=True, cascade="all, delete-orphan")
    user_type = db.relationship('UserType', backref='users', lazy='joined')

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
    response_text = fields.String()  # Include response_text
    response_type = fields.Nested('ResponseTypeSchema', only=['name'])  # Reference ResponseTypeSchema
    settings_selected = fields.String()
    timestamp = fields.DateTime()
    ip_address = fields.String(validate=validate.Length(max=45))
    user_id = fields.UUID()  # Foreign key to User
    showcase = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class Query(db.Model):
    """Query model for storing user queries and their responses."""
    __tablename__ = 'queries'
    __table_args__ = {'schema': 'logs'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    query_text = db.Column(db.Text, nullable=False, comment="Text of the query made by the user")
    response_id = db.Column(db.Integer, db.ForeignKey('logs.responses.id', ondelete='CASCADE'), nullable=True, comment="ID of the response received")
    response_type_id = db.Column(db.Integer, db.ForeignKey('meta.response_types.id', ondelete='SET NULL'), nullable=True, comment="Foreign key to the response type")
    settings_selected = db.Column(db.String(255), nullable=True, comment="Settings used when making the query")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment="Time when query was made")
    ip_address = db.Column(db.String(45), nullable=True, comment="IP address from which the query was made")
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('entities.users.user_id', ondelete='CASCADE'), nullable=False, comment="ID of the user who made the query")
    showcase = db.Column(db.Boolean, default=False, nullable=False, comment="Indicates whether the query is marked for showcase")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record last update date")

    response = db.relationship('Response', back_populates='query', uselist=False)  # Establish a bidirectional relationship with Response
    response_type = db.relationship('ResponseType', lazy='joined')

    def serialize(self):
        """Serialize the Query object to a dictionary."""
        logger.debug(f"Serializing query {self.id}")
        serialized_data = QuerySchema().dump(self)
        serialized_data["response_text"] = self.response.response_text if self.response else None
        return serialized_data

    def __repr__(self):
        return f"<Query {self.id} by User {self.user_id}>"

class Response(db.Model):
    """Response model for storing responses separately if needed."""
    __tablename__ = 'responses'
    __table_args__ = {'schema': 'logs', 'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    response_text = db.Column(db.Text, nullable=False, comment="Response text")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Record last update date")

    query = db.relationship('Query', back_populates='response', uselist=False)  # Establish bidirectional relationship without FK

    def serialize(self):
        """Serialize the Response object to a dictionary."""
        logger.debug(f"Serializing response {self.id}")
        return ResponseSchema().dump(self)

    def __repr__(self):
        return f"<Response {self.id}>"

class ResponseSchema(Schema):
    id = fields.Integer()
    response_text = fields.String(required=True)
    query_id = fields.Integer()  # Foreign key to Query
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class ResponseTypeSchema(Schema):
    id = fields.Integer()
    name = fields.String(required=True)

# ResponseType Definition
class ResponseType(db.Model):
    """ResponseType model to define different response types for queries."""
    __tablename__ = 'response_types'
    __table_args__ = {'schema': 'meta'}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment="Auto incrementing primary key")
    name = db.Column(db.String(255), unique=True, nullable=False, comment="Name of the response type")
    prompt = db.Column(db.String(255), nullable=False, comment="Prompt associated with the response type")
    about = db.Column(db.String(255), nullable=True, comment="Description of the response type")
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="Record last update date")

    def __repr__(self):
        return f"<ResponseType {self.name}>"

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
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record creation date")
    updated_at = db.Column(db.DateTime, default=func.now(), nullable=False, comment="Record last update date")

    def serialize(self):
        """Serialize the Activity object to a dictionary."""
        logger.debug(f"Serializing activity {self.id}")
        return ActivitySchema().dump(self)

    def __repr__(self):
        return f"<Activity {self.id} by User {self.user_id}>"
