# mastermind/utils/token_utils.py
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from .logging import logger

def generate_token(email, salt):
    logger.debug(f"💌 Generating token for email: {email} with salt: {salt}. Enchanted to meet you!")
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        token = serializer.dumps(email, salt=salt)
        logger.info(f"✨ Token generated successfully for email: {email}. It’s a love story!")
        return token
    except Exception as e:
        logger.error(f"😢 Problem generating token for email: {email}. Error: {e}. This love is difficult, but it’s real.")
        raise

def confirm_token(token, salt, expiration=3600):
    logger.debug(f"🔍 Confirming token with salt: {salt} and expiration: {expiration} seconds. Ready for it?")
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=salt, max_age=expiration)
        logger.info(f"✅ Token confirmed successfully for email: {email}. You belong with me!")
        return email
    except Exception as e:
        logger.warning(f"🚫 Token confirmation failed. Error: {e}. And I knew you were trouble when you walked in.")
        return False
