from pydantic import BaseModel, EmailStr
from datetime import datetime

# ------------------ User Schemas ------------------ #
# Schema for user registration
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Schema for user login
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for returning user data in API responses
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic V2 compatibility

# ------------------ Sensor Data Schemas ------------------ #
# Schema for sensor data input (when sending sensor data)
class SensorDataCreate(BaseModel):
    sensor_id: str
    sensor_type: str
    temperature: float
    humidity: float

# Schema for sensor data response (when retrieving stored sensor data)
class SensorDataResponse(SensorDataCreate):
    id: int
    timestamp: datetime | None = None  # Optional timestamp

    class Config:
        from_attributes = True  # Ensures compatibility with SQLAlchemy models

# ------------------ Security Event Schemas (IDS) ------------------ #
# Schema for creating security events
class SecurityEventCreate(BaseModel):
    event_type: str  # "anomaly", "intrusion", "suspicious_login", etc.
    severity: str  # "low", "medium", "high", "critical"
    source_ip: str | None = None
    user_id: int | None = None
    sensor_id: str | None = None
    description: str
    details: str | None = None  # JSON string with additional details

# Schema for security event response
class SecurityEventResponse(SecurityEventCreate):
    id: int
    status: str  # "open", "investigating", "resolved", "false_positive"
    timestamp: datetime
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True

# Schema for updating security event status
class SecurityEventUpdate(BaseModel):
    status: str  # "open", "investigating", "resolved", "false_positive"
    details: str | None = None

# ------------------ Threat Alert Schemas (IPS) ------------------ #
# Schema for creating threat alerts
class ThreatAlertCreate(BaseModel):
    alert_type: str  # "blocked_ip", "rate_limit", "suspicious_activity"
    threat_level: str  # "low", "medium", "high", "critical"
    source_ip: str | None = None
    target_endpoint: str | None = None
    action_taken: str  # "blocked", "rate_limited", "logged", "quarantined"
    description: str
    metadata: str | None = None  # JSON string with additional data

# Schema for threat alert response
class ThreatAlertResponse(ThreatAlertCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ------------------ Audit Log Schemas ------------------ #
# Schema for audit log response
class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    action: str
    endpoint: str | None = None
    method: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    status_code: int | None = None
    success: str
    details: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True

# ------------------ Authorized Device Schemas ------------------ #
# Schema for device registration
class DeviceCreate(BaseModel):
    device_id: str
    device_name: str
    device_type: str  # "sensor", "controller", "gateway"
    mac_address: str | None = None
    location: str | None = None

# Schema for device response
class DeviceResponse(DeviceCreate):
    id: int
    status: str  # "active", "inactive", "suspicious", "quarantined"
    last_seen: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

# Schema for device status update
class DeviceStatusUpdate(BaseModel):
    status: str  # "active", "inactive", "suspicious", "quarantined"

# ------------------ Security Dashboard Schemas ------------------ #
# Schema for security summary response
class SecuritySummary(BaseModel):
    total_events: int
    critical_events: int
    high_priority_events: int
    active_threats: int
    blocked_ips: int
    quarantined_devices: int
    last_24h_events: int

# Schema for anomaly detection results
class AnomalyDetectionResult(BaseModel):
    sensor_id: str
    anomaly_type: str  # "temperature_spike", "humidity_drop", "unusual_pattern"
    severity: str
    current_value: float
    expected_range: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
