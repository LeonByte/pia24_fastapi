# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        cron \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy crontab file
COPY crontab /etc/cron.d/my-cron
RUN chmod 0644 /etc/cron.d/my-cron

# Apply cron job
RUN crontab /etc/cron.d/my-cron

# Expose the port that FastAPI uses (default is 8000)
EXPOSE 8000

# Start supervisord
CMD ["/usr/bin/supervisord"]
