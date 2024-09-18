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

# Start the application
echo "Starting the application..."
exec "$@"
