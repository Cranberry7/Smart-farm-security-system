from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

# SQLAlchemy ORM model for User table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# SQLAlchemy ORM model for SensorData table
class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)  # Unique identifier for the sensor
    sensor_type = Column(String, index=True)  # Type of sensor (e.g., motion, temperature)
    temperature = Column(Float, nullable=True)  # Temperature data
    humidity = Column(Float, nullable=True)  # Humidity data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user_id = Column(Integer, ForeignKey("users.id"))  # Link sensor data to a user (optional)

# SQLAlchemy ORM model for Security Events (IDS)
class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)  # e.g., "anomaly", "intrusion", "suspicious_login"
    severity = Column(String, index=True)  # "low", "medium", "high", "critical"
    source_ip = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sensor_id = Column(String, nullable=True)
    description = Column(String)
    details = Column(String, nullable=True)  # JSON string with additional details
    status = Column(String, default="open")  # "open", "investigating", "resolved", "false_positive"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

# SQLAlchemy ORM model for Threat Alerts (IPS)
class ThreatAlert(Base):
    __tablename__ = "threat_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, index=True)  # "blocked_ip", "rate_limit", "suspicious_activity"
    threat_level = Column(String, index=True)  # "low", "medium", "high", "critical"
    source_ip = Column(String, nullable=True)
    target_endpoint = Column(String, nullable=True)
    action_taken = Column(String)  # "blocked", "rate_limited", "logged", "quarantined"
    description = Column(String)
    metadata = Column(String, nullable=True)  # JSON string with additional data
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# SQLAlchemy ORM model for Audit Logs
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, index=True)  # "login", "logout", "api_call", "data_access"
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)  # HTTP method
    source_ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    success = Column(String, default="true")  # "true", "false"
    details = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

# SQLAlchemy ORM model for Device Authentication (Farm-specific)
class AuthorizedDevice(Base):
    __tablename__ = "authorized_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)  # Unique device identifier
    device_name = Column(String)  # Human-readable name
    device_type = Column(String)  # "sensor", "controller", "gateway"
    mac_address = Column(String, nullable=True)
    location = Column(String, nullable=True)  # Farm section/area
    status = Column(String, default="active")  # "active", "inactive", "suspicious", "quarantined"
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
