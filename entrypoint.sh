#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure required environment variables are set
REQUIRED_VARS=("POSTGRES_DATABASE" "POSTGRES_USER" "POSTGRES_PASSWORD" "LANGFLOW_POSTGRES_PASSWORD" "LANGFUSE_POSTGRES_PASSWORD" "CANDIDATEGPT_POSTGRES_PASSWORD")
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "Error: Environment variable '$VAR' is not set."
    exit 1
  fi
done

# Default to 'db_postgres' if POSTGRES_HOST is not set
POSTGRES_HOST="${POSTGRES_HOST:-db_postgres}"

# Wait for the database to be ready
until PGPASSWORD="$POSTGRES_PASSWORD" pg_isready -h "$POSTGRES_HOST" -p 5432 -d "postgres" -U "$POSTGRES_USER"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Function to create the database and user if they don't exist
create_db_and_user() {
  DB_NAME=$1
  DB_USER=$2
  DB_PASS=$3

  # Check if the database exists
  echo "Checking if '$DB_NAME' database exists..."
  DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")

  if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating '$DB_NAME' database..."
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE $DB_NAME;"
  else
    echo "'$DB_NAME' database already exists."
  fi

  # Check if the user exists
  echo "Checking if user '$DB_USER' exists..."
  USER_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")

  if [ "$USER_EXISTS" != "1" ]; then
    echo "Creating user '$DB_USER'..."
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
  else
    echo "User '$DB_USER' already exists."
  fi

  # Grant privileges to the user for the database
  echo "Granting privileges to '$DB_USER' on '$DB_NAME' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

  # Ensure the user has privileges on the public schema
  echo "Granting schema-level privileges on 'public' schema in '$DB_NAME' for '$DB_USER'..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$DB_NAME" -c "
    GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $DB_USER;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $DB_USER;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO $DB_USER;
  "
}

# Create and configure each database and user
create_db_and_user "langfuse" "langfuse_app" "$LANGFUSE_POSTGRES_PASSWORD"
create_db_and_user "langflow" "langflow_app" "$LANGFLOW_POSTGRES_PASSWORD"
create_db_and_user "candidategpt" "candidategpt_app" "$CANDIDATEGPT_POSTGRES_PASSWORD"

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head


# Start the application
echo "Starting the application..."
exec "$@"
