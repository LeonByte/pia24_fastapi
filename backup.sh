#!/bin/bash

# Set the backup directory (relative to the script location)
BACKUP_DIR="./backups"

# Set the database credentials
DB_USER="postgres"
DB_PASSWORD="password"
DB_NAME="mydatabase"
DB_HOST="db"

# Get the current timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure the backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
  mkdir -p "$BACKUP_DIR"
fi

# Create the backup
BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql.gz"
PGPASSWORD=$DB_PASSWORD pg_dump -U $DB_USER -h $DB_HOST $DB_NAME | gzip > "$BACKUP_FILE"

# Print the result
echo "Backup saved to $BACKUP_FILE"
