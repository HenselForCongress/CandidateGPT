# Use an official Python runtime as a parent image
FROM python:3.12

# Install PostgreSQL client and Poetry
RUN apt-get update && apt-get install -y postgresql-client \
    && pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false

# Create a logs directory in case nothing is mounted...
RUN mkdir /logs

# Create and set working directory
WORKDIR /app

# Copy over the pyproject.toml and poetry.lock file to install dependencies
COPY pyproject.toml poetry.lock* /app/

# Install runtime dependencies using Poetry
RUN poetry install --only main || (poetry lock --no-update && poetry install --only main)

# Copy the rest of the code
COPY . /app/


# Copy the entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint.sh executable
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Command to run the application
CMD ["python3", "-m", "run"]
