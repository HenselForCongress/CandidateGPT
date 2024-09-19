#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure required environment variables are set
REQUIRED_VARS=("POSTGRES_DATABASE" "POSTGRES_USER" "POSTGRES_PASSWORD" "LANGFLOW_POSTGRES_USER" "LANGFLOW_POSTGRES_PASSWORD")
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

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head


# Create CandidateGPT Database user so not using root

echo "Creating user '$CANDIDATEGPT_POSTGRES_USER'..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE USER $CANDIDATEGPT_POSTGRES_USER WITH PASSWORD '$CANDIDATEGPT_POSTGRES_PASSWORD';"

# Grant privileges to candidategpt user for gpt database
echo "Granting privileges to '$LANGFUSE_POSTGRES_USER' on 'langfuse' database..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "GRANT ALL PRIVILEGES ON DATABASE langfuse TO $LANGFUSE_POSTGRES_USER;"


# Check if langfuse database exists
echo "Checking if 'langfuse' database exists..."
DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='langfuse'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Creating 'langfuse' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE langfuse;"

  # Create new user for langfuse
  echo "Creating user '$LANGFUSE_POSTGRES_USER'..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE USER $LANGFUSE_POSTGRES_USER WITH PASSWORD '$LANGFUSE_POSTGRES_PASSWORD';"

  # Grant privileges to langfuse user for langfuse database
  echo "Granting privileges to '$LANGFUSE_POSTGRES_USER' on 'langfuse' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "GRANT ALL PRIVILEGES ON DATABASE langfuse TO $LANGFUSE_POSTGRES_USER;"

  echo "'langfuse' database and user created successfully."
else
  echo "'langfuse' database already exists. Skipping creation."
fi


# Check if langflow database exists
echo "Checking if 'langflow' database exists..."
DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='langflow'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Creating 'langflow' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE langflow;"

  # Create new user for langflow
  echo "Creating user '$LANGFLOW_POSTGRES_USER'..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE USER $LANGFLOW_POSTGRES_USER WITH PASSWORD '$LANGFLOW_POSTGRES_PASSWORD';"

  # Grant privileges to langflow user for langflow database
  echo "Granting privileges to '$LANGFLOW_POSTGRES_USER' on 'langflow' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "GRANT ALL PRIVILEGES ON DATABASE langflow TO $LANGFLOW_POSTGRES_USER;"

  echo "'langflow' database and user created successfully."
else
  echo "'langflow' database already exists. Skipping creation."
fi





# Start the application
echo "Starting the application..."
exec "$@"
