from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.anomaly_detection import anomaly_detector

router = APIRouter(tags=["Sensor Data"])

# ✅ Route to receive and store sensor data (with anomaly detection)
@router.post("/add", response_model=schemas.SensorDataResponse)
def create_sensor_data(
    sensor_data: schemas.SensorDataCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Basic validation
        if sensor_data.temperature < -50 or sensor_data.temperature > 100:
            raise HTTPException(status_code=400, detail="Temperature out of valid range")
        if sensor_data.humidity < 0 or sensor_data.humidity > 100:
            raise HTTPException(status_code=400, detail="Humidity out of valid range")
        
        # Check for data flooding (IPS feature)
        if anomaly_detector.detect_data_flooding(db, sensor_data.sensor_id):
            # Log security event
            client_ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
            anomaly_detector.create_security_event_from_anomaly(
                db,
                schemas.AnomalyDetectionResult(
                    sensor_id=sensor_data.sensor_id,
                    anomaly_type="data_flooding",
                    severity="high",
                    current_value=1.0,  # Rate limit exceeded
                    expected_range="Within rate limits",
                    confidence=1.0,
                    timestamp=datetime.utcnow()
                ),
                source_ip=client_ip
            )
            raise HTTPException(status_code=429, detail="Too many requests from this sensor")
            
        # Store the sensor data
        new_data = models.SensorData(**sensor_data.dict())
        db.add(new_data)
        db.commit()
        db.refresh(new_data)
        
        # Run anomaly detection on the new data
        try:
            anomalies = anomaly_detector.detect_sensor_anomalies(db, new_data)
            
            # Create security events for detected anomalies
            client_ip = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
            for anomaly in anomalies:
                anomaly_detector.create_security_event_from_anomaly(db, anomaly, source_ip=client_ip)
                
        except Exception as anomaly_error:
            # Don't fail the request if anomaly detection fails
            print(f"Anomaly detection error: {anomaly_error}")
        
        return new_data
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add sensor data: {str(e)}")

# ✅ Route to get all sensor data
@router.get("/", response_model=list[schemas.SensorDataResponse])
def get_sensor_data(db: Session = Depends(get_db)):
    return db.query(models.SensorData).all()

# ✅ Optional: Check if sensor API is working
@router.get("/status")
def get_status():
    return {"message": "Sensor API is working"}