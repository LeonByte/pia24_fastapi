import psutil
import requests
import time
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Discord Webhook URL from .env
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Lowered thresholds for testing
THRESHOLDS = {
    'cpu': 1.0,    # CPU usage in percentage (lowered to 1%)
    'memory': 1.0, # Memory usage in percentage (lowered to 1%)
    'disk': 1.0,   # Disk usage in percentage (lowered to 1%)
    'ssh_attempts': 1  # Number of failed SSH attempts (lowered to 1)
}

# Track the last alerts with shorter cooldown for testing
last_alerts = {
    'cpu': 0,
    'memory': 0,
    'disk': 0,
    'ssh': 0
}
ALERT_COOLDOWN = 3  # Lowered to 3 seconds for faster testing

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
        
        # Filtrera för rader som innehåller "Authentication failed" eller "Connection closed by authenticating user"
        failed_attempts = [log for log in logs if "Authentication failed" in log or "Connection closed by authenticating user" in log]
        
        if len(failed_attempts) >= THRESHOLDS['ssh_attempts']:
            current_time = time.time()
            if current_time - last_alerts['ssh'] > ALERT_COOLDOWN:
                last_alerts['ssh'] = current_time
                return f"🚨 SSH alert: {len(failed_attempts)} failed login attempts\n" \
                       f"Recent attempts:\n" + "\n".join(failed_attempts[-3:])
    except Exception as e:
        return f"⚠️ Error checking SSH logs: {str(e)}"
    return None


# def check_ssh_logs():
#     """Monitors SSH logs for failed login attempts on Ubuntu"""
#     try:
#         # Läs /var/log/auth.log och sök efter misslyckade SSH-inloggningar
#         with open('/var/log/auth.log', 'r') as log_file:
#             logs = log_file.readlines()
        
#         # Filtrera för rader som innehåller "Failed password"
#         failed_attempts = [log for log in logs if "Failed password" in log]
        
#         if len(failed_attempts) >= THRESHOLDS['ssh_attempts']:
#             current_time = time.time()
#             if current_time - last_alerts['ssh'] > ALERT_COOLDOWN:
#                 last_alerts['ssh'] = current_time
#                 return f"🚨 SSH alert: {len(failed_attempts)} failed login attempts\n" \
#                        f"Recent attempts:\n" + "\n".join(failed_attempts[-3:])
#     except Exception as e:
#         return f"⚠️ Error checking SSH logs: {str(e)}"
#     return None

# def check_ssh_logs():
#     """Monitors SSH logs for failed login attempts"""
#     try:
#         result = subprocess.run(
#             ['log', 'show', '--predicate', 'eventMessage contains "Failed password"', '--last', '5m'],
#             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5
#         )
        
#         logs = result.stdout.decode('utf-8')
#         failed_attempts = logs.splitlines()
        
#         if len(failed_attempts) >= THRESHOLDS['ssh_attempts']:
#             current_time = time.time()
#             if current_time - last_alerts['ssh'] > ALERT_COOLDOWN:
#                 last_alerts['ssh'] = current_time
#                 return f"🚨 SSH alert: {len(failed_attempts)} failed login attempts\n" \
#                        f"Recent attempts:\n" + "\n".join(failed_attempts[-3:])
#     except Exception as e:
#         return f"⚠️ Error checking SSH logs: {str(e)}"
#     return None

def send_discord_alert(message):
    """Sends alerts to Discord"""
    if not message or not DISCORD_WEBHOOK_URL:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"**System Alert - {timestamp}**\n{message}"
    
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
            time.sleep(3)

if __name__ == "__main__":
    try:
        monitor_system()
    except KeyboardInterrupt:
        print("\nExiting system monitoring...")
