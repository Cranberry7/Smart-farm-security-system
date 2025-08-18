from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(tags=["Device Management"])

# ✅ Register new authorized device
@router.post("/register", response_model=schemas.DeviceResponse)
def register_device(
    device_data: schemas.DeviceCreate,
    db: Session = Depends(get_db)
):
    """Register a new authorized device for the farm"""
    # Check if device already exists
    existing_device = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.device_id == device_data.device_id
    ).first()
    
    if existing_device:
        raise HTTPException(status_code=400, detail="Device already registered")
    
    # Create new device
    new_device = models.AuthorizedDevice(
        device_id=device_data.device_id,
        device_name=device_data.device_name,
        device_type=device_data.device_type,
        mac_address=device_data.mac_address,
        location=device_data.location,
        status="active",
        last_seen=datetime.utcnow()
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    return new_device

# ✅ Get all authorized devices
@router.get("/", response_model=List[schemas.DeviceResponse])
def get_all_devices(
    status: str = None,
    device_type: str = None,
    db: Session = Depends(get_db)
):
    """Get all authorized devices with optional filtering"""
    query = db.query(models.AuthorizedDevice)
    
    if status:
        query = query.filter(models.AuthorizedDevice.status == status)
    if device_type:
        query = query.filter(models.AuthorizedDevice.device_type == device_type)
    
    devices = query.order_by(desc(models.AuthorizedDevice.last_seen)).all()
    return devices

# ✅ Get device by ID
@router.get("/{device_id}", response_model=schemas.DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)):
    """Get specific device details"""
    device = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.device_id == device_id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

# ✅ Update device status
@router.patch("/{device_id}/status")
def update_device_status(
    device_id: str,
    status_update: schemas.DeviceStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update device status (active, inactive, suspicious, quarantined)"""
    device = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.device_id == device_id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    old_status = device.status
    device.status = status_update.status
    device.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(device)
    
    # Log security event if device is quarantined or marked suspicious
    if status_update.status in ["quarantined", "suspicious"]:
        security_event = models.SecurityEvent(
            event_type="device_status_change",
            severity="medium" if status_update.status == "suspicious" else "high",
            description=f"Device {device_id} status changed from {old_status} to {status_update.status}",
            details=f"{{\"device_id\": \"{device_id}\", \"old_status\": \"{old_status}\", \"new_status\": \"{status_update.status}\"}}",
            status="open"
        )
        db.add(security_event)
        db.commit()
    
    return {"message": f"Device status updated to {status_update.status}"}

# ✅ Validate sensor data against authorized devices
@router.post("/validate-sensor/{sensor_id}")
def validate_sensor_device(sensor_id: str, db: Session = Depends(get_db)):
    """Validate if a sensor is from an authorized device"""
    device = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.device_id == sensor_id,
        models.AuthorizedDevice.device_type.in_(["sensor", "gateway"])
    ).first()
    
    if not device:
        return {
            "authorized": False,
            "message": "Sensor not found in authorized devices",
            "action": "register_device_or_block"
        }
    
    if device.status == "quarantined":
        return {
            "authorized": False,
            "message": "Device is quarantined",
            "action": "block_data"
        }
    
    if device.status == "suspicious":
        return {
            "authorized": True,
            "message": "Device marked as suspicious - monitoring enhanced",
            "action": "allow_with_monitoring"
        }
    
    # Update last seen timestamp
    device.last_seen = datetime.utcnow()
    db.commit()
    
    return {
        "authorized": True,
        "message": "Device authorized",
        "device_info": {
            "name": device.device_name,
            "type": device.device_type,
            "location": device.location,
            "last_seen": device.last_seen
        }
    }

# ✅ Get device activity summary
@router.get("/activity/summary")
def get_device_activity_summary(days: int = 7, db: Session = Depends(get_db)):
    """Get device activity summary for the last N days"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total devices by status
    device_status_counts = db.query(
        models.AuthorizedDevice.status,
        func.count(models.AuthorizedDevice.id).label('count')
    ).group_by(models.AuthorizedDevice.status).all()
    
    # Devices by type
    device_type_counts = db.query(
        models.AuthorizedDevice.device_type,
        func.count(models.AuthorizedDevice.id).label('count')
    ).group_by(models.AuthorizedDevice.device_type).all()
    
    # Recently active devices (last seen within timeframe)
    active_devices = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.last_seen >= start_date
    ).count()
    
    # Inactive devices (not seen recently)
    inactive_devices = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.last_seen < start_date
    ).count()
    
    return {
        "period_days": days,
        "total_devices": db.query(models.AuthorizedDevice).count(),
        "active_devices": active_devices,
        "inactive_devices": inactive_devices,
        "device_status_breakdown": [
            {"status": row.status, "count": row.count} 
            for row in device_status_counts
        ],
        "device_type_breakdown": [
            {"type": row.device_type, "count": row.count} 
            for row in device_type_counts
        ]
    }

# ✅ Check for unauthorized sensor activity
@router.get("/security/unauthorized-sensors")
def check_unauthorized_sensors(db: Session = Depends(get_db)):
    """Check for sensor data from unauthorized devices"""
    # Get all unique sensor IDs from recent data (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    sensor_ids_in_data = db.query(models.SensorData.sensor_id).filter(
        models.SensorData.timestamp >= yesterday
    ).distinct().all()
    
    # Get all authorized device IDs
    authorized_device_ids = db.query(models.AuthorizedDevice.device_id).all()
    authorized_set = {device_id[0] for device_id in authorized_device_ids}
    
    # Find unauthorized sensors
    unauthorized_sensors = []
    for (sensor_id,) in sensor_ids_in_data:
        if sensor_id not in authorized_set:
            # Count recent data points from this sensor
            data_count = db.query(models.SensorData).filter(
                models.SensorData.sensor_id == sensor_id,
                models.SensorData.timestamp >= yesterday
            ).count()
            
            unauthorized_sensors.append({
                "sensor_id": sensor_id,
                "data_points": data_count,
                "first_seen": db.query(models.SensorData).filter(
                    models.SensorData.sensor_id == sensor_id
                ).order_by(models.SensorData.timestamp).first().timestamp,
                "last_seen": db.query(models.SensorData).filter(
                    models.SensorData.sensor_id == sensor_id
                ).order_by(desc(models.SensorData.timestamp)).first().timestamp
            })
    
    # Create security events for unauthorized sensors
    for sensor_info in unauthorized_sensors:
        existing_event = db.query(models.SecurityEvent).filter(
            models.SecurityEvent.event_type == "unauthorized_device",
            models.SecurityEvent.sensor_id == sensor_info["sensor_id"],
            models.SecurityEvent.status == "open"
        ).first()
        
        if not existing_event:  # Only create if no open event exists
            security_event = models.SecurityEvent(
                event_type="unauthorized_device",
                severity="high",
                sensor_id=sensor_info["sensor_id"],
                description=f"Unauthorized sensor detected: {sensor_info['sensor_id']}",
                details=f"{{\"sensor_id\": \"{sensor_info['sensor_id']}\", \"data_points\": {sensor_info['data_points']}}}",
                status="open"
            )
            db.add(security_event)
    
    db.commit()
    
    return {
        "unauthorized_sensors_found": len(unauthorized_sensors),
        "unauthorized_sensors": unauthorized_sensors,
        "recommendation": "Review and either authorize these devices or block their data"
    }

# ✅ Get device health status
@router.get("/health/status")
def get_device_health_status(db: Session = Depends(get_db)):
    """Get overall device health status"""
    now = datetime.utcnow()
    
    # Define time thresholds
    last_hour = now - timedelta(hours=1)
    last_day = now - timedelta(days=1)
    last_week = now - timedelta(weeks=1)
    
    # Count devices by last seen status
    devices_last_hour = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.last_seen >= last_hour,
        models.AuthorizedDevice.status == "active"
    ).count()
    
    devices_last_day = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.last_seen >= last_day,
        models.AuthorizedDevice.last_seen < last_hour,
        models.AuthorizedDevice.status == "active"
    ).count()
    
    devices_offline = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.last_seen < last_day,
        models.AuthorizedDevice.status == "active"
    ).count()
    
    quarantined_devices = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.status == "quarantined"
    ).count()
    
    suspicious_devices = db.query(models.AuthorizedDevice).filter(
        models.AuthorizedDevice.status == "suspicious"
    ).count()
    
    total_devices = db.query(models.AuthorizedDevice).count()
    
    # Calculate health score (0-100)
    if total_devices > 0:
        health_score = max(0, min(100, 
            (devices_last_hour * 100 + devices_last_day * 70) / total_devices - 
            (quarantined_devices * 20) - (suspicious_devices * 10)
        ))
    else:
        health_score = 0
    
    return {
        "overall_health_score": round(health_score, 1),
        "total_devices": total_devices,
        "devices_online_last_hour": devices_last_hour,
        "devices_online_last_day": devices_last_day,
        "devices_offline": devices_offline,
        "quarantined_devices": quarantined_devices,
        "suspicious_devices": suspicious_devices,
        "health_status": "excellent" if health_score >= 90 else 
                        "good" if health_score >= 70 else 
                        "warning" if health_score >= 50 else "critical"
    }
