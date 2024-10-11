# tests/test_connections.py
import os
import psycopg2

# Test database connection
try:
    logger.info("Testing database connection...")
    test_db_connection()
except Exception as e:
    logger.error("Database connection test failed.", exc_info=True)
    raise


def test_db_connection():
    """Test the database connection."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
        )
        conn.close()
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Error connecting to the database: {str(e)}", exc_info=True)
        raise



