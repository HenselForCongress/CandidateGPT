# mastermind/utils/sentry.py
# Setup sentry
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .logging import logger


# TODO

    try:
        sentry_sdk.init(
            dsn=os.getenv('SENRTY_DSN'),
            traces_sample_rate=1.0,
            integrations=[FlaskIntegration()],
            sample_rate=0.25,
            profiles_sample_rate=1.0,
        )
        logger.info("Sentry SDK initialized.")
    except Exception as e:
        logger.error(f"Error initializing Sentry SDK: {str(e)}", exc_info=True)
        raise
