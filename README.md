# Smart Farm Security & Monitoring System 

## Overview

The Smart Farm Security & Monitoring System is an advanced platform designed to safeguard agricultural environments by integrating Intrusion Detection (IDS) and Intrusion Prevention (IPS) capabilities. Building on traditional farm monitoring, this system goes beyond environmental data tracking to proactively identify, analyze, and respond to security threats targeting farm sensors, devices, and network infrastructure.

Leveraging real-time anomaly detection, device authentication, and comprehensive security middleware, the platform provides continuous protection against both physical and cyber intrusions. It monitors sensor data integrity, detects unusual activity patterns, enforces strict access controls, and automatically mitigates risks through intelligent response mechanisms such as IP blocking and device quarantine.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Farm Sensors  │ -> │  Security       │ -> │  FastAPI        │
│   & Devices     │    │  Middleware     │    │  Backend        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                  |
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Anomaly        │ <- │  PostgreSQL     │
                       │  Detection      │    │  Database       │
                       └─────────────────┘    └─────────────────┘
                                  |
                       ┌─────────────────┐
                       │  Security       │
                       │  Dashboard      │
                       └─────────────────┘
```

## Database Schema

### Core Tables:
- **users** - User accounts and authentication
- **sensor_data** - Farm sensor readings and measurements
- **security_events** - IDS security incidents and anomalies
- **threat_alerts** - IPS threat notifications and responses
- **audit_logs** - Complete system access and activity logs
- **authorized_devices** - Registered farm devices and sensors

## Security Features in Detail

### **Anomaly Detection Engine**
- **Temperature Anomalies**: Critical high (>45°C), Critical low (<-10°C)
- **Humidity Anomalies**: Critical high (>95%), Critical low (<15%)
- **Rapid Change Detection**: Detects unusual sensor value changes (>15°C in 10 minutes)
- **Pattern Analysis**: Identifies identical readings (replay attacks), unrealistic precision
- **Data Flooding Detection**: Rate limiting for sensor data submissions

### **Security Middleware**
- **Real-time Request Monitoring** - All API calls logged and analyzed
- **Rate Limiting by Endpoint** - Different limits for login, sensor data, and general API
- **Automatic IP Blocking** - Progressive blocking based on suspicious activity patterns
- **Authentication Attempt Tracking** - Failed login monitoring and response
- **Response Time Analysis** - Performance-based threat detection

### **Device Security**
- **Device Registration System** - Whitelist of authorized farm equipment
- **Status Management** - Active, Suspicious, Quarantined device states
- **Unauthorized Device Detection** - Automatic identification of rogue sensors
- **Health Monitoring** - Device connectivity and status tracking

## Monitoring & Alerting

### **Security Dashboard Features:**
- Real-time threat level assessment
- Security event timeline and statistics
- Device health and status overview
- Anomaly detection results
- Active threat monitoring
- System performance metrics

### **Alert Types:**
- 🔴 **Critical**: System breaches, device compromises
- 🟠 **High**: Suspicious activities, unauthorized devices
- 🟡 **Medium**: Rate limit violations, unusual patterns  
- ⚪ **Low**: Informational security events

## 🚀 Getting Started

### **Prerequisites:**
- Python 3.8+
- PostgreSQL 12+
- Required packages (see `requirements.txt`)

### **Installation:**

1. **Clone and setup:**
```bash
git clone <repository>
cd smart_farm_backend
pip install -r requirements.txt
```

2. **Database setup:**
```bash
# Update .env with your PostgreSQL credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smart_farm_db
DB_USER=postgres
DB_PASSWORD=your_password
SECRET_KEY=your_jwt_secret_key_here
```

3. **Run the application:**
```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run with Python
python -m app.main
```

4. **Launch Security Dashboard:**
```bash
# Run the enhanced security dashboard
python -c "from app.dashboard import run_security_dashboard; run_security_dashboard()"

# Or run basic dashboard
python app/dashboard.py
```

### **API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing Security Features

### **Test Anomaly Detection:**
```bash
# Send extreme temperature reading
curl -X POST "http://localhost:8000/sensor/add" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "test_sensor_1",
    "sensor_type": "temperature",
    "temperature": 50.0,
    "humidity": 45.0
  }'

# Check security events
curl "http://localhost:8000/security/events?severity=critical"
```

### **Test Rate Limiting:**
```bash
# Rapidly send requests to trigger rate limiting
for i in {1..10}; do
  curl -X POST "http://localhost:8000/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "wrong"}' &
done
```

### **Device Management:**
```bash
# Register authorized device
curl -X POST "http://localhost:8000/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "farm_sensor_001",
    "device_name": "Greenhouse Temperature Sensor",
    "device_type": "sensor",
    "location": "Greenhouse A"
  }'

# Check for unauthorized devices
curl "http://localhost:8000/devices/security/unauthorized-sensors"
```

## Key Metrics

The system tracks and provides analytics on:
- **Security Events**: Total events, severity distribution, trends
- **Device Health**: Online/offline status, health scores
- **Threat Intelligence**: IP reputation, attack patterns
- **System Performance**: API response times, data processing rates
- **Anomaly Detection**: Detection accuracy, false positive rates

## Configuration

### **Security Thresholds** (in `anomaly_detection.py`):
- Temperature: Critical (-10°C to 45°C), Warning (5°C to 35°C)
- Humidity: Critical (15% to 95%), Warning (25% to 85%)
- Rate Limits: Login (5/5min), Sensor Data (60/min), General (100/min)

### **IPS Actions**:
- Automatic IP blocking after 5 rate limit violations
- Device quarantine for repeated anomalies
- Login lockout after 10 failed attempts 

## Future Enhancements

Potential expansions include:
- Machine learning-based anomaly detection
- Integration with external threat intelligence feeds
- Mobile app for security monitoring
- Email/SMS alert notifications
- Advanced visualization dashboards
- Multi-farm management capabilities

---
