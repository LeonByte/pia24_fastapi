# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        cron \
        supervisor \
        gcc \
        python3-dev \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port that FastAPI uses (default is 8000)
EXPOSE 8000

# Copy the health monitoring script
COPY health_monitor.py /app/health_monitor.py

# Ensure the health monitoring script is executable
RUN chmod +x /app/health_monitor.py

# Install cron
RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

# Add crontab file
COPY crontab /etc/cron.d/health-monitor-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/health-monitor-cron

# Apply cron job
RUN crontab /etc/cron.d/health-monitor-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start cron and the FastAPI app & Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

