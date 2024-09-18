#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Wait for the database to be ready
until pg_isready -h db_postgres -p 5432 -d "$POSTGRES_DATABASE" -U "$POSTGRES_USER"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Create the langfuse database if it doesn't already exist
echo "Checking if 'langfuse' database exists..."
DB_EXISTS=$(psql -h db_postgres -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='langfuse'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Creating 'langfuse' database..."
  psql -h db_postgres -U "$POSTGRES_USER" -c "CREATE DATABASE langfuse;"
else
  echo "'langfuse' database already exists. Skipping creation."
fi

# Start the application
echo "Starting the application..."
exec "$@"
