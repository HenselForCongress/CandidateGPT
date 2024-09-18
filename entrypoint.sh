#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure required environment variables are set
REQUIRED_VARS=("POSTGRES_DATABASE" "POSTGRES_USER" "POSTGRES_PASSWORD")
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

# Create the langfuse database if it doesn't already exist
echo "Checking if 'langfuse' database exists..."
DB_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='langfuse'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Creating 'langfuse' database..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE langfuse;"
else
  echo "'langfuse' database already exists. Skipping creation."
fi

# Start the application
echo "Starting the application..."
exec "$@"
