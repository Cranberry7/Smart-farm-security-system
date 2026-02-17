# Backend Connection Guide

This document explains how to connect the Flutter frontend to the FastAPI backend.

## Prerequisites

1. **Backend Server Running**: Make sure your FastAPI backend is running on `http://localhost:8000`
2. **Dependencies Installed**: Run `flutter pub get` to install required packages

## Configuration

### Automatic Platform Detection

The API base URL is now **automatically configured** based on the platform:

- **Android Emulator**: `http://10.0.2.2:8000` (automatically detected)
- **iOS Simulator**: `http://localhost:8000` (automatically detected)
- **Physical Device/Other**: `http://192.168.56.1:8000` (default fallback)

### Manual Override for Physical Devices

If you're testing on a physical device, you can manually override the base URL:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

To find your computer's IP:
- **Windows**: Run `ipconfig` in CMD and look for IPv4 Address
- **Mac/Linux**: Run `ifconfig` or `ip addr` and look for inet address

## Features Implemented

### 1. Authentication
- ✅ Login with username and password
- ✅ Registration with username, email, and password
- ✅ JWT token storage and automatic inclusion in API requests
- ✅ Auto-login check on app startup
- ✅ Logout functionality

### 2. Home Dashboard
- ✅ Real-time security summary from backend
- ✅ Connected devices list with status indicators
- ✅ Recent threat alerts display
- ✅ Pull-to-refresh functionality
- ✅ Loading states and error handling

### 3. Sensor Data Page
- ✅ Fetch all sensor readings from backend
- ✅ Display latest readings per sensor
- ✅ Temperature and humidity data
- ✅ Timestamp formatting (relative time)
- ✅ Summary statistics
- ✅ Pull-to-refresh functionality

### 4. User Profile Page
- ✅ Display user information from stored data
- ✅ User ID and creation date (if available from API)
- ✅ Fallback to stored username/email if API unavailable

## API Endpoints Used

- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `GET /sensor/` - Get all sensor data
- `GET /security/summary` - Get security summary
- `GET /security/alerts` - Get threat alerts
- `GET /devices/` - Get all devices
- `GET /users/me` - Get current authenticated user profile
- `GET /users/` - Get users (for profile)

## Testing the Connection

1. **Start Backend**:
   ```bash
   cd Smart-farm-security-system
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Run Flutter App**:
   ```bash
   cd login_ui
   flutter run
   ```

3. **Test Login**:
   - Register a new user or use existing credentials
   - Login should redirect to dashboard
   - Dashboard should show real data from backend

## Troubleshooting

### Connection Refused Error
- Ensure backend is running on port 8000
- Check firewall settings
- Verify the base URL matches your environment

### 401 Unauthorized Errors
- Token might have expired - try logging out and logging back in
- Check if token is being stored correctly

### CORS Issues
- Backend should have CORS middleware configured (already in `app/main.py`)
- If issues persist, check backend CORS settings

### No Data Displayed
- Check backend logs for errors
- Verify database has data (sensor readings, devices, etc.)
- Check network tab in browser/dev tools for API responses

## Next Steps

To enhance the integration:
1. Add real-time updates using WebSockets
2. Implement push notifications for critical alerts
3. Add offline data caching
4. Implement token refresh mechanism
5. Add more detailed error messages

