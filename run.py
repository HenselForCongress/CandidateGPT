# run.py
import os
from mastermind import begin_era, logger

def main():
    app = begin_era()


    logger.info("🚀 Jack is writing...")
    try:
        # Hosting the Flask application
        # Set the Flask environment to development
        app.config['ENV'] = 'development'
        app.config['DEBUG'] = True
        app.run(host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('APP_PORT', 5024)))
    except Exception as e:
        logger.error("💥 An unexpected error occurred: %s", str(e), exc_info=True)

if __name__ == "__main__":
    main()
