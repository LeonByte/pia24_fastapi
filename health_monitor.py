import psutil
import requests
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta


# Load environment variables from .env file
load_dotenv()

# Discord Webhook URL from .env
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Lowered thresholds for testing
THRESHOLDS = {
    'cpu': 10.0,    # CPU usage in percentage
    'memory': 50.0, # Memory usage in percentage
    'disk': 20.0,   # Disk usage in percentage
    'ssh_attempts': 1  # Number of failed SSH attempts
}

# Track the last alerts with shorter cooldown for testing
last_alerts = {
    'cpu': 0,
    'memory': 0,
    'disk': 0,
    'ssh': 0
}
ALERT_COOLDOWN = 10  # Lowered to 10 seconds for faster testing

def check_cpu():
    """Monitors CPU usage"""
    cpu_percent = psutil.cpu_percent(interval=0.1)  # Faster CPU check for testing
    if cpu_percent > THRESHOLDS['cpu']:
        current_time = time.time()
        if current_time - last_alerts['cpu'] > ALERT_COOLDOWN:
            last_alerts['cpu'] = current_time
            return f"🚨 CPU usage: {cpu_percent}% (Threshold: {THRESHOLDS['cpu']}%)"
    return None

def check_memory():
    """Monitors memory usage"""
    memory = psutil.virtual_memory()
    if memory.percent > THRESHOLDS['memory']:
        current_time = time.time()
        if current_time - last_alerts['memory'] > ALERT_COOLDOWN:
            last_alerts['memory'] = current_time
            return f"🚨 Memory usage: {memory.percent}% (Threshold: {THRESHOLDS['memory']}%)\n" \
                   f"Used: {memory.used / (1024**3):.1f}GB out of {memory.total / (1024**3):.1f}GB"
    return None

def check_disk():
    """Monitors disk usage"""
    disk = psutil.disk_usage('/')
    if disk.percent > THRESHOLDS['disk']:
        current_time = time.time()
        if current_time - last_alerts['disk'] > ALERT_COOLDOWN:
            last_alerts['disk'] = current_time
            return f"🚨 Disk usage: {disk.percent}% (Threshold: {THRESHOLDS['disk']}%)\n" \
                   f"Used: {disk.used / (1024**3):.1f}GB out of {disk.total / (1024**3):.1f}GB"
    return None

def check_ssh_logs():
    """Monitors SSH logs for failed login attempts when using SSH keys"""
    try:
        # Läs /var/log/auth.log och sök efter misslyckade SSH-inloggningar
        with open('/var/log/auth.log', 'r') as log_file:
            logs = log_file.readlines()

        # Reverse the logs so we check the latest entries
        logs.reverse()
        
        # Filter out the last failed attempt that we have already processed
        failed_attempts = [log for log in logs if "Invalid user" in log or "Connection closed by invalid user" in log]
        
        # If there's a new failed attempt, check if we need to send an alert
        if failed_attempts:
            last_failed_attempt = failed_attempts[0]  # The latest failed attempt
            last_failed_timestamp = last_failed_attempt.split(' ')[0]  # Get the timestamp of the last failed attempt

            # Convert the timestamp from UTC to Stockholm time (UTC+1 or UTC+2 depending on daylight saving time)
            utc_time = datetime.strptime(last_failed_timestamp, "%Y-%m-%dT%H:%M:%S.%f+00:00")
            
            # Stockholm time zone offset is UTC+1 (CET) or UTC+2 (CEST) based on the date
            now = datetime.now()

            # Determine if today is in DST period for Stockholm (CEST or CET)
            if now.month > 3 and now.month < 10:
                # This is the period when DST (CEST - UTC+2) is active
                stockholm_offset = timedelta(hours=2)  # UTC+2 (CEST)
            else:
                # Outside of DST period, use UTC+1 (CET)
                stockholm_offset = timedelta(hours=1)  # UTC+1 (CET)

            # Apply the Stockholm time zone offset to the UTC time
            stockholm_time = utc_time + stockholm_offset

            # Format the local time for display (alert timestamp)
            formatted_alert_time = stockholm_time.strftime("%Y-%m-%d %H:%M:%S")

            # Format the recent failed attempt timestamp in Stockholm time
            recent_attempt_time = utc_time + stockholm_offset
            formatted_recent_attempt_time = recent_attempt_time.strftime("%Y-%m-%d %H:%M:%S")

            # We only send an alert if the last failed attempt was not already sent
            if last_failed_timestamp != last_alerts['ssh']:
                last_alerts['ssh'] = last_failed_timestamp
                return f"🚨 SSH alert: {len(failed_attempts)} failed login attempt(s)\n" \
                       f"*Stockholm Timestamp: **{formatted_alert_time}***\n" \
                       f"Recent attempt:\n{formatted_recent_attempt_time} {failed_attempts[0]}"
    except Exception as e:
        return f"⚠️ Error checking SSH logs: {str(e)}"
    
    return None

def send_discord_alert(message):
    """Sends alerts to Discord"""
    if not message or not DISCORD_WEBHOOK_URL:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"**System Alert - {timestamp} UTC**\n{message}"
    
    payload = {
        'content': formatted_message
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(f"Alert sent to Discord: {message}")
        else:
            print(f"Error sending to Discord: {response.status_code}")
    except Exception as e:
        print(f"Failed to send to Discord: {str(e)}")

def generate_system_report():
    """Generates a complete system report"""
    cpu = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    report = "**📊 System Status**\n"
    report += f"CPU: {cpu}% (Threshold: {THRESHOLDS['cpu']}%)\n"
    report += f"Memory: {memory.percent}% (Threshold: {THRESHOLDS['memory']}%)\n"
    report += f"Disk: {disk.percent}% (Threshold: {THRESHOLDS['disk']}%)"
    
    return report

def monitor_system():
    """Main function for system monitoring"""
    print("Starting system monitoring with lowered thresholds for testing...")
    print(f"CPU Threshold: {THRESHOLDS['cpu']}%")
    print(f"Memory Threshold: {THRESHOLDS['memory']}%")
    print(f"Disk Threshold: {THRESHOLDS['disk']}%")
    print(f"SSH Threshold: {THRESHOLDS['ssh_attempts']} attempts")
    
    # Send initial system report
    send_discord_alert(generate_system_report())
    
    while True:
        try:
            # Check all systems and collect alerts
            alerts = []
            for check in [check_cpu, check_memory, check_disk, check_ssh_logs]:
                result = check()
                if result:
                    alerts.append(result)
            
            # Send alerts if any were found
            if alerts:
                send_discord_alert("\n\n".join(alerts))
            
            # Short wait time for faster testing
            time.sleep(3)
            
        except Exception as e:
            print(f"Error in monitoring loop: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    try:
        monitor_system()
    except KeyboardInterrupt:
        print("\nExiting system monitoring...")
