from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app import models, schemas
from app.anomaly_detection import anomaly_detector

router = APIRouter(tags=["Security Monitoring"])

# ✅ Get all security events (IDS)
@router.get("/events", response_model=List[schemas.SecurityEventResponse])
def get_security_events(
    skip: int = 0, 
    limit: int = 100,
    severity: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get security events with optional filtering"""
    query = db.query(models.SecurityEvent)
    
    if severity:
        query = query.filter(models.SecurityEvent.severity == severity)
    if status:
        query = query.filter(models.SecurityEvent.status == status)
    
    events = query.order_by(desc(models.SecurityEvent.timestamp)).offset(skip).limit(limit).all()
    return events

# ✅ Get security event by ID
@router.get("/events/{event_id}", response_model=schemas.SecurityEventResponse)
def get_security_event(event_id: int, db: Session = Depends(get_db)):
    """Get specific security event details"""
    event = db.query(models.SecurityEvent).filter(models.SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Security event not found")
    return event

# ✅ Update security event status
@router.patch("/events/{event_id}")
def update_security_event_status(
    event_id: int,
    update_data: schemas.SecurityEventUpdate,
    db: Session = Depends(get_db)
):
    """Update security event status (resolve, mark as false positive, etc.)"""
    event = db.query(models.SecurityEvent).filter(models.SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Security event not found")
    
    event.status = update_data.status
    if update_data.details:
        event.details = update_data.details
    
    if update_data.status == "resolved":
        event.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(event)
    return {"message": "Security event updated successfully"}

# ✅ Get threat alerts (IPS)
@router.get("/alerts", response_model=List[schemas.ThreatAlertResponse])
def get_threat_alerts(
    skip: int = 0,
    limit: int = 100,
    threat_level: str = None,
    db: Session = Depends(get_db)
):
    """Get threat alerts with optional filtering"""
    query = db.query(models.ThreatAlert)
    
    if threat_level:
        query = query.filter(models.ThreatAlert.threat_level == threat_level)
    
    alerts = query.order_by(desc(models.ThreatAlert.timestamp)).offset(skip).limit(limit).all()
    return alerts

# ✅ Get audit logs
@router.get("/audit-logs", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: str = None,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """Get audit logs with optional filtering"""
    query = db.query(models.AuditLog)
    
    if action:
        query = query.filter(models.AuditLog.action == action)
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    
    logs = query.order_by(desc(models.AuditLog.timestamp)).offset(skip).limit(limit).all()
    return logs

# ✅ Security summary dashboard
@router.get("/summary", response_model=schemas.SecuritySummary)
def get_security_summary(db: Session = Depends(get_db)):
    """Get security summary for dashboard"""
    # Get current time for 24h calculation
    current_time = datetime.utcnow()
    yesterday = current_time - timedelta(days=1)
    
    # Count various security metrics
    total_events = db.query(models.SecurityEvent).count()
    critical_events = db.query(models.SecurityEvent).filter(models.SecurityEvent.severity == "critical").count()
    high_priority_events = db.query(models.SecurityEvent).filter(models.SecurityEvent.severity == "high").count()
    
    # Active threats (open events with high/critical severity)
    active_threats = db.query(models.SecurityEvent).filter(
        models.SecurityEvent.status == "open",
        models.SecurityEvent.severity.in_(["high", "critical"])
    ).count()
    
    # Blocked IPs (count unique IPs from threat alerts)
    blocked_ips = db.query(models.ThreatAlert).filter(
        models.ThreatAlert.action_taken == "blocked"
    ).with_entities(models.ThreatAlert.source_ip).distinct().count()
    
    # Quarantined devices
    quarantined_devices = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.status == "quarantined"
    ).count()
    
    # Events in last 24 hours
    last_24h_events = db.query(models.SecurityEvent).filter(
        models.SecurityEvent.timestamp >= yesterday
    ).count()
    
    return schemas.SecuritySummary(
        total_events=total_events,
        critical_events=critical_events,
        high_priority_events=high_priority_events,
        active_threats=active_threats,
        blocked_ips=blocked_ips,
        quarantined_devices=quarantined_devices,
        last_24h_events=last_24h_events
    )

# ✅ Run anomaly detection on specific sensor
@router.post("/analyze-sensor/{sensor_id}")
def analyze_sensor_for_anomalies(sensor_id: str, db: Session = Depends(get_db)):
    """Run anomaly detection analysis on a specific sensor"""
    # Get recent sensor data
    recent_data = db.query(models.SensorData).filter(
        models.SensorData.sensor_id == sensor_id
    ).order_by(desc(models.SensorData.timestamp)).limit(10).all()
    
    if not recent_data:
        raise HTTPException(status_code=404, detail="No data found for this sensor")
    
    all_anomalies = []
    
    # Run anomaly detection on recent readings
    for reading in recent_data:
        anomalies = anomaly_detector.detect_sensor_anomalies(db, reading)
        all_anomalies.extend(anomalies)
    
    # Run pattern analysis
    pattern_anomalies = anomaly_detector.detect_suspicious_patterns(db, sensor_id)
    all_anomalies.extend(pattern_anomalies)
    
    # Create security events for any anomalies found
    for anomaly in all_anomalies:
        anomaly_detector.create_security_event_from_anomaly(db, anomaly)
    
    return {
        "message": f"Analysis complete. Found {len(all_anomalies)} anomalies.",
        "anomalies": all_anomalies,
        "sensor_id": sensor_id
    }

# ✅ Run full system analysis
@router.post("/analyze-all")
def analyze_all_sensors(db: Session = Depends(get_db)):
    """Run anomaly detection on all sensors"""
    # Get all unique sensor IDs from recent data (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    sensor_ids = db.query(models.SensorData.sensor_id).filter(
        models.SensorData.timestamp >= yesterday
    ).distinct().all()
    
    total_anomalies = 0
    analyzed_sensors = 0
    
    for (sensor_id,) in sensor_ids:
        try:
            # Get recent readings for this sensor
            recent_readings = db.query(models.SensorData).filter(
                models.SensorData.sensor_id == sensor_id,
                models.SensorData.timestamp >= yesterday
            ).order_by(desc(models.SensorData.timestamp)).limit(5).all()
            
            sensor_anomalies = []
            
            # Analyze each reading
            for reading in recent_readings:
                anomalies = anomaly_detector.detect_sensor_anomalies(db, reading)
                sensor_anomalies.extend(anomalies)
            
            # Analyze patterns
            pattern_anomalies = anomaly_detector.detect_suspicious_patterns(db, sensor_id)
            sensor_anomalies.extend(pattern_anomalies)
            
            # Create security events
            for anomaly in sensor_anomalies:
                anomaly_detector.create_security_event_from_anomaly(db, anomaly)
            
            total_anomalies += len(sensor_anomalies)
            analyzed_sensors += 1
            
        except Exception as e:
            print(f"Error analyzing sensor {sensor_id}: {e}")
            continue
    
    return {
        "message": "Full system analysis complete",
        "analyzed_sensors": analyzed_sensors,
        "total_anomalies_found": total_anomalies,
        "timestamp": datetime.utcnow().isoformat()
    }

# ✅ Get security statistics by time period
@router.get("/statistics")
def get_security_statistics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get security statistics for a time period"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Events by severity
    events_by_severity = db.query(
        models.SecurityEvent.severity,
        func.count(models.SecurityEvent.id).label('count')
    ).filter(
        models.SecurityEvent.timestamp >= start_date
    ).group_by(models.SecurityEvent.severity).all()
    
    # Events by type
    events_by_type = db.query(
        models.SecurityEvent.event_type,
        func.count(models.SecurityEvent.id).label('count')
    ).filter(
        models.SecurityEvent.timestamp >= start_date
    ).group_by(models.SecurityEvent.event_type).all()
    
    # Daily event counts
    daily_events = db.query(
        func.date(models.SecurityEvent.timestamp).label('date'),
        func.count(models.SecurityEvent.id).label('count')
    ).filter(
        models.SecurityEvent.timestamp >= start_date
    ).group_by(func.date(models.SecurityEvent.timestamp)).all()
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "events_by_severity": [{"severity": row.severity, "count": row.count} for row in events_by_severity],
        "events_by_type": [{"event_type": row.event_type, "count": row.count} for row in events_by_type],
        "daily_events": [{"date": str(row.date), "count": row.count} for row in daily_events]
    }

# ✅ Get top threat sources
@router.get("/threat-sources")
def get_top_threat_sources(limit: int = 10, db: Session = Depends(get_db)):
    """Get top IP addresses generating security events"""
    threat_sources = db.query(
        models.SecurityEvent.source_ip,
        func.count(models.SecurityEvent.id).label('event_count'),
        func.max(models.SecurityEvent.severity).label('max_severity')
    ).filter(
        models.SecurityEvent.source_ip.isnot(None)
    ).group_by(
        models.SecurityEvent.source_ip
    ).order_by(
        desc(func.count(models.SecurityEvent.id))
    ).limit(limit).all()
    
    return [
        {
            "source_ip": row.source_ip,
            "event_count": row.event_count,
            "max_severity": row.max_severity
        }
        for row in threat_sources
    ]
