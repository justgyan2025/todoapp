FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define the command to run the application
CMD gunicorn --bind :\$PORT --workers 3 --threads 2 app:app
