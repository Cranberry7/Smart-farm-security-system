import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from . import models, schemas
from .database import SessionLocal
from .security import decode_token

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for IDS/IPS functionality"""
    
    def __init__(self, app):
        super().__init__(app)
        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage = defaultdict(list)
        self.blocked_ips = set()
        self.suspicious_activities = defaultdict(int)
        
        # Rate limit thresholds
        self.rate_limits = {
            "/auth/login": {"limit": 5, "window": 300},  # 5 attempts per 5 minutes
            "/sensor/add": {"limit": 60, "window": 60},   # 60 requests per minute
            "default": {"limit": 100, "window": 60}       # 100 requests per minute default
        }

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return JSONResponse(
                status_code=403,
                content={"detail": "IP address blocked due to suspicious activity"}
            )
        
        # Start timing the request
        start_time = time.time()
        
        # Rate limiting check
        if self.is_rate_limited(request, client_ip):
            # Log the rate limiting event
            self.log_security_event(
                event_type="rate_limit_exceeded",
                severity="medium",
                source_ip=client_ip,
                description=f"Rate limit exceeded for endpoint {request.url.path}",
                endpoint=str(request.url.path),
                method=request.method
            )
            
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
        
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log the request
        await self.log_api_request(request, response, client_ip, process_time)
        
        # Check for suspicious patterns
        await self.analyze_request_patterns(request, response, client_ip)
        
        return response

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"

    def is_rate_limited(self, request: Request, client_ip: str) -> bool:
        """Check if request should be rate limited"""
        endpoint = request.url.path
        current_time = time.time()
        
        # Get rate limit configuration for this endpoint
        rate_config = self.rate_limits.get(endpoint, self.rate_limits["default"])
        limit = rate_config["limit"]
        window = rate_config["window"]
        
        # Clean old requests outside the time window
        cutoff_time = current_time - window
        self.rate_limit_storage[f"{client_ip}:{endpoint}"] = [
            req_time for req_time in self.rate_limit_storage[f"{client_ip}:{endpoint}"]
            if req_time > cutoff_time
        ]
        
        # Check if limit is exceeded
        requests_in_window = len(self.rate_limit_storage[f"{client_ip}:{endpoint}"])
        
        if requests_in_window >= limit:
            # Increment suspicious activity counter
            self.suspicious_activities[client_ip] += 1
            
            # Block IP if too many rate limit violations
            if self.suspicious_activities[client_ip] >= 5:
                self.blocked_ips.add(client_ip)
                self.log_security_event(
                    event_type="ip_blocked",
                    severity="high",
                    source_ip=client_ip,
                    description=f"IP blocked due to repeated rate limit violations",
                    action_taken="blocked"
                )
            
            return True
        
        # Add current request to the list
        self.rate_limit_storage[f"{client_ip}:{endpoint}"].append(current_time)
        return False

    async def log_api_request(self, request: Request, response, client_ip: str, process_time: float):
        """Log API request for audit trail"""
        try:
            # Extract user info from JWT token if present
            user_id = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                decoded = decode_token(token)
                if "user_id" in decoded and "error" not in decoded:
                    user_id = decoded["user_id"]
            
            # Determine success based on status code
            success = "true" if response.status_code < 400 else "false"
            
            # Create audit log entry
            db = SessionLocal()
            try:
                audit_log = models.AuditLog(
                    user_id=user_id,
                    action="api_call",
                    endpoint=str(request.url.path),
                    method=request.method,
                    source_ip=client_ip,
                    user_agent=request.headers.get("User-Agent"),
                    status_code=response.status_code,
                    success=success,
                    details=json.dumps({
                        "query_params": dict(request.query_params),
                        "response_time": round(process_time, 3),
                        "content_length": response.headers.get("content-length", "0")
                    })
                )
                
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
                
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Error logging API request: {e}")

    async def analyze_request_patterns(self, request: Request, response, client_ip: str):
        """Analyze request patterns for suspicious activity"""
        try:
            # Check for failed authentication attempts
            if (request.url.path == "/auth/login" and 
                response.status_code == 401):
                
                self.suspicious_activities[f"{client_ip}:failed_login"] += 1
                
                # Check if too many failed attempts
                if self.suspicious_activities[f"{client_ip}:failed_login"] >= 5:
                    self.log_security_event(
                        event_type="suspicious_login",
                        severity="high",
                        source_ip=client_ip,
                        description=f"Multiple failed login attempts from {client_ip}",
                        endpoint="/auth/login"
                    )
                    
                    # Consider blocking after many failed attempts
                    if self.suspicious_activities[f"{client_ip}:failed_login"] >= 10:
                        self.blocked_ips.add(client_ip)
                        self.log_security_event(
                            event_type="ip_blocked",
                            severity="critical",
                            source_ip=client_ip,
                            description=f"IP blocked due to {self.suspicious_activities[f'{client_ip}:failed_login']} failed login attempts",
                            action_taken="blocked"
                        )
            
            # Check for scanning behavior (many 404s)
            if response.status_code == 404:
                self.suspicious_activities[f"{client_ip}:404s"] += 1
                
                if self.suspicious_activities[f"{client_ip}:404s"] >= 20:
                    self.log_security_event(
                        event_type="potential_scanning",
                        severity="medium",
                        source_ip=client_ip,
                        description=f"Potential scanning behavior: {self.suspicious_activities[f'{client_ip}:404s']} 404 responses",
                        endpoint=str(request.url.path)
                    )
            
            # Check for unusual User-Agent strings
            user_agent = request.headers.get("User-Agent", "").lower()
            suspicious_agents = ["bot", "crawler", "spider", "scanner", "curl", "wget"]
            
            if any(agent in user_agent for agent in suspicious_agents):
                self.log_security_event(
                    event_type="suspicious_user_agent",
                    severity="low",
                    source_ip=client_ip,
                    description=f"Suspicious User-Agent detected: {user_agent[:100]}",
                    endpoint=str(request.url.path)
                )
                
        except Exception as e:
            print(f"Error analyzing request patterns: {e}")

    def log_security_event(self, event_type: str, severity: str, source_ip: str, 
                          description: str, **kwargs):
        """Log security event to database"""
        try:
            db = SessionLocal()
            try:
                # Create security event
                security_event = models.SecurityEvent(
                    event_type=event_type,
                    severity=severity,
                    source_ip=source_ip,
                    description=description,
                    details=json.dumps(kwargs) if kwargs else None,
                    status="open"
                )
                
                db.add(security_event)
                db.commit()
                
                # If it's a critical event, also create a threat alert
                if severity in ["critical", "high"]:
                    threat_alert = models.ThreatAlert(
                        alert_type=event_type,
                        threat_level=severity,
                        source_ip=source_ip,
                        target_endpoint=kwargs.get("endpoint"),
                        action_taken=kwargs.get("action_taken", "logged"),
                        description=description,
                        metadata=json.dumps(kwargs) if kwargs else None
                    )
                    
                    db.add(threat_alert)
                    db.commit()
                    
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error logging security event: {e}")

    def reset_rate_limits(self):
        """Reset rate limiting data (can be called periodically)"""
        current_time = time.time()
        
        # Clean up old entries
        for key in list(self.rate_limit_storage.keys()):
            self.rate_limit_storage[key] = [
                req_time for req_time in self.rate_limit_storage[key]
                if current_time - req_time < 3600  # Keep last hour
            ]
            
            # Remove empty entries
            if not self.rate_limit_storage[key]:
                del self.rate_limit_storage[key]
        
        # Reset suspicious activity counters (decay over time)
        for key in list(self.suspicious_activities.keys()):
            self.suspicious_activities[key] = max(0, self.suspicious_activities[key] - 1)
            if self.suspicious_activities[key] == 0:
                del self.suspicious_activities[key]
