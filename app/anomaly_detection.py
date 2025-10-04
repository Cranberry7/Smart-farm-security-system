import statistics
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from . import models, schemas

# Import ML libraries
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy.stats import percentileofscore

class AnomalyDetector:
    """Farm-specific anomaly detection engine for IDS functionality"""
    
    def __init__(self):
        # Thresholds for different anomaly types
        self.temperature_thresholds = {
            "critical_high": 45.0,
            "critical_low": -10.0,
            "warning_high": 35.0,
            "warning_low": 5.0,
            "normal_range": (15.0, 30.0)
        }
        
        self.humidity_thresholds = {
            "critical_high": 95.0,
            "critical_low": 15.0,
            "warning_high": 85.0,
            "warning_low": 25.0,
            "normal_range": (40.0, 70.0)
        }
        
        # Rate limits for detecting flooding attacks
        self.rate_limits = {
            "sensor_data_per_minute": 20,
            "api_calls_per_minute": 60,
            "login_attempts_per_hour": 10
        }

        # ML model for anomaly detection
        self.model = IsolationForest(contamination='auto', random_state=42)
        self.scaler = StandardScaler()
        self.model_trained = False
        self.training_scores = []

    def train_model(self, db: Session):
        """Train the anomaly detection model with historical data"""
        historical_data = self._prepare_data_for_training(db)
        
        if len(historical_data) < 100:
            # Not enough data to train a reliable model
            self.model_trained = False
            return

        # Prepare data and train the model
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Feature engineering
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        features = df[['temperature', 'humidity', 'hour_of_day', 'day_of_week']]
        self.scaler.fit(features)
        scaled_features = self.scaler.transform(features)
        
        self.model.fit(scaled_features)
        self.training_scores = self.model.decision_function(scaled_features)
        self.model_trained = True

    def _prepare_data_for_training(self, db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """Fetch and prepare historical data for model training"""
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Fetch historical data from the database
        readings = db.query(models.SensorData).filter(
            models.SensorData.timestamp >= time_threshold
        ).all()
        
        # Convert to a list of dictionaries
        return [
            {
                "temperature": r.temperature,
                "humidity": r.humidity,
                "timestamp": r.timestamp
            }
            for r in readings
        ]

    def detect_sensor_anomalies(self, db: Session, sensor_data: models.SensorData) -> List[schemas.AnomalyDetectionResult]:
        """Detect anomalies using the ML model or fallback to rule-based system"""
        if not self.model_trained:
            # Fallback to the old rule-based system if the model is not trained
            return self._detect_anomalies_rule_based(db, sensor_data)

        # Use the ML model for anomaly detection
        return self._detect_anomalies_ml(db, sensor_data)

    def _detect_anomalies_ml(self, db: Session, sensor_data: models.SensorData) -> List[schemas.AnomalyDetectionResult]:
        """Detect anomalies using the trained Isolation Forest model"""
        anomalies = []
        current_time = datetime.utcnow()

        # Prepare the input for the model
        df = pd.DataFrame([{
            "temperature": sensor_data.temperature,
            "humidity": sensor_data.humidity,
            "timestamp": current_time
        }])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek

        features = df[['temperature', 'humidity', 'hour_of_day', 'day_of_week']]
        scaled_features = self.scaler.transform(features)

        # Predict anomaly (-1 for anomalies, 1 for normal)
        prediction = self.model.predict(scaled_features)

        if prediction[0] == -1:
            # Anomaly detected by the model
            score = self.model.decision_function(scaled_features)[0]
            
            # Calculate confidence based on the percentile of the score in the distribution of anomaly scores
            anomaly_scores = self.training_scores[self.training_scores < 0]
            if len(anomaly_scores) > 0:
                confidence = 1 - (percentileofscore(anomaly_scores, score) / 100)
            else:
                confidence = 1.0 # No anomalies in training data

            confidence = np.clip(confidence, 0, 1) # Ensure confidence is within [0, 1]

            anomaly = schemas.AnomalyDetectionResult(
                sensor_id=sensor_data.sensor_id,
                anomaly_type="ml_detected_anomaly",
                severity="medium",
                current_value=f"Temp: {sensor_data.temperature}°C, Humidity: {sensor_data.humidity}%",
                expected_range="Normal operating conditions",
                confidence=confidence,
                timestamp=current_time
            )
            anomalies.append(anomaly)

        # Also run other checks like rapid changes and data flooding
        rapid_change_anomalies = self._detect_rapid_changes(db, sensor_data)
        anomalies.extend(rapid_change_anomalies)

        return anomalies

    def _detect_anomalies_rule_based(self, db: Session, sensor_data: models.SensorData) -> List[schemas.AnomalyDetectionResult]:
        """Original rule-based anomaly detection"""
        anomalies = []
        
        # Temperature anomaly detection
        temp_anomaly = self._check_temperature_anomaly(sensor_data.temperature, sensor_data.sensor_id)
        if temp_anomaly:
            anomalies.append(temp_anomaly)
            
        # Humidity anomaly detection
        humidity_anomaly = self._check_humidity_anomaly(sensor_data.humidity, sensor_data.sensor_id)
        if humidity_anomaly:
            anomalies.append(humidity_anomaly)
            
        # Rapid change detection (compare with recent readings)
        rapid_change_anomalies = self._detect_rapid_changes(db, sensor_data)
        anomalies.extend(rapid_change_anomalies)
        
        return anomalies

    def _check_temperature_anomaly(self, temperature: float, sensor_id: str) -> schemas.AnomalyDetectionResult | None:
        """Check for temperature-based anomalies"""
        severity = None
        anomaly_type = None
        confidence = 0.0
        
        if temperature >= self.temperature_thresholds["critical_high"]:
            severity = "critical"
            anomaly_type = "critical_temperature_high"
            confidence = 0.95
        elif temperature <= self.temperature_thresholds["critical_low"]:
            severity = "critical"
            anomaly_type = "critical_temperature_low"
            confidence = 0.95
        elif temperature >= self.temperature_thresholds["warning_high"]:
            severity = "high"
            anomaly_type = "high_temperature_warning"
            confidence = 0.75
        elif temperature <= self.temperature_thresholds["warning_low"]:
            severity = "high"
            anomaly_type = "low_temperature_warning"
            confidence = 0.75
        
        if severity:
            return schemas.AnomalyDetectionResult(
                sensor_id=sensor_id,
                anomaly_type=anomaly_type,
                severity=severity,
                current_value=temperature,
                expected_range=f"{self.temperature_thresholds['normal_range'][0]}°C - {self.temperature_thresholds['normal_range'][1]}°C",
                confidence=confidence,
                timestamp=datetime.utcnow()
            )
        
        return None

    def _check_humidity_anomaly(self, humidity: float, sensor_id: str) -> schemas.AnomalyDetectionResult | None:
        """Check for humidity-based anomalies"""
        severity = None
        anomaly_type = None
        confidence = 0.0
        
        if humidity >= self.humidity_thresholds["critical_high"]:
            severity = "critical"
            anomaly_type = "critical_humidity_high"
            confidence = 0.95
        elif humidity <= self.humidity_thresholds["critical_low"]:
            severity = "critical"
            anomaly_type = "critical_humidity_low"
            confidence = 0.95
        elif humidity >= self.humidity_thresholds["warning_high"]:
            severity = "high"
            anomaly_type = "high_humidity_warning"
            confidence = 0.75
        elif humidity <= self.humidity_thresholds["warning_low"]:
            severity = "high"
            anomaly_type = "low_humidity_warning"
            confidence = 0.75
        
        if severity:
            return schemas.AnomalyDetectionResult(
                sensor_id=sensor_id,
                anomaly_type=anomaly_type,
                severity=severity,
                current_value=humidity,
                expected_range=f"{self.humidity_thresholds['normal_range'][0]}% - {self.humidity_thresholds['normal_range'][1]}%",
                confidence=confidence,
                timestamp=datetime.utcnow()
            )
        
        return None

    def _detect_rapid_changes(self, db: Session, current_reading: models.SensorData) -> List[schemas.AnomalyDetectionResult]:
        """Detect rapid changes that might indicate tampering or malfunction"""
        anomalies = []
        
        # Get recent readings from the same sensor (last 10 minutes)
        time_threshold = datetime.utcnow() - timedelta(minutes=10)
        recent_readings = db.query(models.SensorData).filter(
            models.SensorData.sensor_id == current_reading.sensor_id,
            models.SensorData.timestamp >= time_threshold,
            models.SensorData.id != current_reading.id
        ).order_by(models.SensorData.timestamp.desc()).limit(5).all()
        
        if len(recent_readings) >= 2:
            # Calculate average of recent readings
            avg_temp = statistics.mean([r.temperature for r in recent_readings])
            avg_humidity = statistics.mean([r.humidity for r in recent_readings])
            
            # Check for rapid temperature change (>15°C in 10 minutes)
            temp_change = abs(current_reading.temperature - avg_temp)
            if temp_change > 15.0:
                anomalies.append(schemas.AnomalyDetectionResult(
                    sensor_id=current_reading.sensor_id,
                    anomaly_type="rapid_temperature_change",
                    severity="high",
                    current_value=current_reading.temperature,
                    expected_range=f"Within ±10°C of recent average ({avg_temp:.1f}°C)",
                    confidence=0.85,
                    timestamp=datetime.utcnow()
                ))
            
            # Check for rapid humidity change (>30% in 10 minutes)
            humidity_change = abs(current_reading.humidity - avg_humidity)
            if humidity_change > 30.0:
                anomalies.append(schemas.AnomalyDetectionResult(
                    sensor_id=current_reading.sensor_id,
                    anomaly_type="rapid_humidity_change",
                    severity="high",
                    current_value=current_reading.humidity,
                    expected_range=f"Within ±20% of recent average ({avg_humidity:.1f}%)",
                    confidence=0.85,
                    timestamp=datetime.utcnow()
                ))
        
        return anomalies

    def detect_data_flooding(self, db: Session, sensor_id: str, time_window_minutes: int = 1) -> bool:
        """Detect if a sensor is sending data too frequently (potential DoS attack)"""
        time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        count = db.query(models.SensorData).filter(
            models.SensorData.sensor_id == sensor_id,
            models.SensorData.timestamp >= time_threshold
        ).count()
        
        return count > self.rate_limits["sensor_data_per_minute"]

    def detect_suspicious_patterns(self, db: Session, sensor_id: str) -> List[schemas.AnomalyDetectionResult]:
        """Detect suspicious patterns that might indicate manipulation"""
        anomalies = []
        
        # Get readings from the last hour
        time_threshold = datetime.utcnow() - timedelta(hours=1)
        recent_readings = db.query(models.SensorData).filter(
            models.SensorData.sensor_id == sensor_id,
            models.SensorData.timestamp >= time_threshold
        ).order_by(models.SensorData.timestamp.desc()).all()
        
        if len(recent_readings) >= 10:
            # Check for identical readings (possible replay attack)
            identical_count = 0
            for i in range(1, len(recent_readings)):
                if (recent_readings[i].temperature == recent_readings[0].temperature and
                    recent_readings[i].humidity == recent_readings[0].humidity):
                    identical_count += 1
            
            if identical_count >= 5:  # 5+ identical readings in an hour
                anomalies.append(schemas.AnomalyDetectionResult(
                    sensor_id=sensor_id,
                    anomaly_type="identical_readings_pattern",
                    severity="medium",
                    current_value=recent_readings[0].temperature,
                    expected_range="Variable readings expected",
                    confidence=0.80,
                    timestamp=datetime.utcnow()
                ))
            
            # Check for unrealistic precision (all readings end in .0)
            precise_readings = sum(1 for r in recent_readings[:10] 
                                 if r.temperature % 1 == 0 and r.humidity % 1 == 0)
            
            if precise_readings >= 8:  # 8/10 readings have no decimal places
                anomalies.append(schemas.AnomalyDetectionResult(
                    sensor_id=sensor_id,
                    anomaly_type="unrealistic_precision_pattern",
                    severity="medium",
                    current_value=recent_readings[0].temperature,
                    expected_range="Natural sensor variation expected",
                    confidence=0.70,
                    timestamp=datetime.utcnow()
                ))
        
        return anomalies

    def create_security_event_from_anomaly(self, db: Session, anomaly: schemas.AnomalyDetectionResult, 
                                         source_ip: str = None) -> models.SecurityEvent:
        """Convert anomaly detection result to security event"""
        severity_mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        
        details = {
            "anomaly_type": anomaly.anomaly_type,
            "current_value": anomaly.current_value,
            "expected_range": anomaly.expected_range,
            "confidence": anomaly.confidence,
            "detection_timestamp": anomaly.timestamp.isoformat()
        }
        
        security_event = models.SecurityEvent(
            event_type="anomaly",
            severity=severity_mapping.get(anomaly.severity, "medium"),
            source_ip=source_ip,
            sensor_id=anomaly.sensor_id,
            description=f"Anomaly detected: {anomaly.anomaly_type} in sensor {anomaly.sensor_id}",
            details=json.dumps(details),
            status="open"
        )
        
        db.add(security_event)
        db.commit()
        db.refresh(security_event)
        
        return security_event

# Global anomaly detector instance
anomaly_detector = AnomalyDetector()