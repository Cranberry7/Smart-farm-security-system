import requests
import time
import random
import json
import os
from datetime import datetime
from typing import Dict, List

API_URL = "http://localhost:8000"

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    """Display dashboard header"""
    print("=" * 80)
    print(f"{'SMART FARM MONITORING SYSTEM':^80}")
    print(f"{'Live Sensor Data Dashboard':^80}")
    print(f"{'Last Updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
    print("=" * 80)

def send_sensor_data():
    """Generate and send random sensor data"""
    url = f"{API_URL}/sensor/add"
    
    # Generate random sensor data
    data = {
        "sensor_id": f"sensor_{random.randint(1, 3)}",
        "sensor_type": random.choice(["temperature", "humidity", "combined"]),
        "temperature": round(random.uniform(18.0, 32.0), 1),
        "humidity": round(random.uniform(40.0, 85.0), 1)
    }
    
    try:
        response = requests.post(url, json=data)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def get_sensor_data():
    """Fetch all sensor data"""
    url = f"{API_URL}/sensor/"
    
    try:
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

def display_latest_readings(data):
    """Display the latest readings for each sensor"""
    # Group by sensor_id and get latest reading
    latest_readings = {}
    
    for reading in data:
        sensor_id = reading["sensor_id"]
        timestamp = reading.get("timestamp")
        
        if sensor_id not in latest_readings or timestamp > latest_readings[sensor_id]["timestamp"]:
            latest_readings[sensor_id] = reading
    
    # Display latest readings
    print("\nLATEST SENSOR READINGS:")
    print("-" * 80)
    print(f"{'SENSOR ID':<15}{'TYPE':<15}{'TEMPERATURE':<15}{'HUMIDITY':<15}{'TIMESTAMP':<20}")
    print("-" * 80)
    
    for sensor_id, reading in latest_readings.items():
        print(f"{reading['sensor_id']:<15}{reading['sensor_type']:<15}{reading['temperature']:<15.1f}{reading['humidity']:<15.1f}{reading.get('timestamp', 'N/A'):<20}")

def display_stats(data):
    """Display statistics from sensor data"""
    if not data:
        print("\nNo sensor data available")
        return
    
    # Calculate stats
    temps = [reading["temperature"] for reading in data]
    humidities = [reading["humidity"] for reading in data]
    
    avg_temp = sum(temps) / len(temps) if temps else 0
    avg_humidity = sum(humidities) / len(humidities) if humidities else 0
    max_temp = max(temps) if temps else 0
    min_temp = min(temps) if temps else 0
    max_humidity = max(humidities) if humidities else 0
    min_humidity = min(humidities) if humidities else 0
    
    print("\nSYSTEM STATISTICS:")
    print("-" * 80)
    print(f"Total Readings: {len(data)}")
    print(f"Average Temperature: {avg_temp:.1f}°C")
    print(f"Average Humidity: {avg_humidity:.1f}%")
    print(f"Temperature Range: {min_temp:.1f}°C - {max_temp:.1f}°C")
    print(f"Humidity Range: {min_humidity:.1f}% - {max_humidity:.1f}%")

def get_security_summary():
    """Fetch security summary from API"""
    url = f"{API_URL}/security/summary"
    
    try:
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def get_recent_security_events():
    """Fetch recent security events"""
    url = f"{API_URL}/security/events?limit=5"
    
    try:
        response = requests.get(url)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

def display_security_status():
    """Display security monitoring status"""
    security_summary = get_security_summary()
    recent_events = get_recent_security_events()
    
    print("\nSECURITY STATUS:")
    print("-" * 80)
    
    if security_summary:
        print(f"Total Security Events: {security_summary.get('total_events', 0)}")
        print(f"Critical Events: {security_summary.get('critical_events', 0)}")
        print(f"Active Threats: {security_summary.get('active_threats', 0)}")
        print(f"Blocked IPs: {security_summary.get('blocked_ips', 0)}")
        print(f"Events (24h): {security_summary.get('last_24h_events', 0)}")
        
        # Display threat level
        active_threats = security_summary.get('active_threats', 0)
        if active_threats >= 5:
            print("🔴 THREAT LEVEL: HIGH")
        elif active_threats >= 2:
            print("🟡 THREAT LEVEL: MEDIUM")
        else:
            print("🟢 THREAT LEVEL: LOW")
    else:
        print("Security monitoring unavailable")
    
    # Display recent security events
    if recent_events:
        print("\nRECENT SECURITY EVENTS:")
        print("-" * 80)
        for event in recent_events[:3]:  # Show only top 3
            severity_icon = {
                "critical": "🔴",
                "high": "🟠", 
                "medium": "🟡",
                "low": "⚪"
            }.get(event.get('severity', 'low'), "⚪")
            
            print(f"{severity_icon} {event.get('event_type', 'unknown').upper()}: {event.get('description', 'No description')[:50]}...")

def display_alerts(data):
    """Display any alerts based on sensor readings"""
    if not data:
        return
    
    alerts = []
    
    # Check last 5 readings for alert conditions
    recent_readings = sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
    
    for reading in recent_readings:
        if reading["temperature"] > 30:
            alerts.append(f"HIGH TEMPERATURE ALERT: {reading['sensor_id']} reported {reading['temperature']}°C")
        elif reading["temperature"] < 15:
            alerts.append(f"LOW TEMPERATURE ALERT: {reading['sensor_id']} reported {reading['temperature']}°C")
            
        if reading["humidity"] > 80:
            alerts.append(f"HIGH HUMIDITY ALERT: {reading['sensor_id']} reported {reading['humidity']}%")
        elif reading["humidity"] < 30:
            alerts.append(f"LOW HUMIDITY ALERT: {reading['sensor_id']} reported {reading['humidity']}%")
    
    if alerts:
        print("\nSENSOR ALERTS:")
        print("-" * 80)
        for alert in alerts:
            print(f"⚠️  {alert}")

def run_security_dashboard():
    """Run the enhanced security monitoring dashboard"""
    try:
        while True:
            # Generate new sensor data
            send_sensor_data()
            
            # Get all sensor data
            data = get_sensor_data()
            
            # Display dashboard
            clear_screen()
            display_header()
            display_latest_readings(data)
            display_stats(data)
            display_security_status()  # New security monitoring
            display_alerts(data)
            
            print("\n" + "="*80)
            print("SMART FARM SECURITY & MONITORING SYSTEM - IDS/IPS ENABLED")
            print("Press Ctrl+C to exit...")
            time.sleep(5)  # Slightly longer refresh for security data
    except KeyboardInterrupt:
        print("\nSecurity Dashboard stopped")

def run_dashboard():
    """Run the live dashboard"""
    try:
        while True:
            # Generate new sensor data
            send_sensor_data()
            
            # Get all sensor data
            data = get_sensor_data()
            
            # Display dashboard
            clear_screen()
            display_header()
            display_latest_readings(data)
            display_stats(data)
            display_alerts(data)
            
            print("\nPress Ctrl+C to exit...")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nDashboard stopped")

if __name__ == "__main__":
    run_dashboard()