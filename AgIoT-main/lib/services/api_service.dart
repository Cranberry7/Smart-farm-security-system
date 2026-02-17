import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/token_storage.dart';

class ApiService {
  // Update this to match your backend URL
  static const String baseUrl = 'http://192.168.56.1:8000';
  // For Android emulator, use: 'http://10.0.2.2:8000'
  // For iOS simulator, use: 'http://localhost:8000'
  // For physical device, use your computer's IP: 'http://192.168.x.x:8000'

  final TokenStorage _tokenStorage = TokenStorage();

  // Get headers with authentication token
  Future<Map<String, String>> _getHeaders({bool includeAuth = true}) async {
    Map<String, String> headers = {
      'Content-Type': 'application/json',
    };

    if (includeAuth) {
      final token = await _tokenStorage.getToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }

    return headers;
  }

  // Handle API errors
  void _handleError(http.Response response) {
    if (response.statusCode >= 400) {
      try {
        final errorData = json.decode(response.body);
        throw Exception(errorData['detail'] ?? 'An error occurred');
      } catch (e) {
        throw Exception('Error: ${response.statusCode} - ${response.body}');
      }
    }
  }

  // ============ Authentication ============
  Future<Map<String, dynamic>> login(String username, String password) async {
    final url = Uri.parse('$baseUrl/auth/login');
    final response = await http.post(
      url,
      headers: await _getHeaders(includeAuth: false),
      body: json.encode({
        'username': username,
        'password': password,
      }),
    );

    _handleError(response);
    final data = json.decode(response.body);
    
    // Store token
    if (data['access_token'] != null) {
      await _tokenStorage.saveToken(data['access_token']);
    }

    return data;
  }

  Future<Map<String, dynamic>> register(
      String username, String email, String password) async {
    final url = Uri.parse('$baseUrl/auth/register');
    final response = await http.post(
      url,
      headers: await _getHeaders(includeAuth: false),
      body: json.encode({
        'username': username,
        'email': email,
        'password': password,
      }),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  Future<void> logout() async {
    await _tokenStorage.deleteToken();
  }

  // ============ Sensor Data ============
  Future<List<dynamic>> getSensorData() async {
    final url = Uri.parse('$baseUrl/sensor/');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> addSensorData(
      String sensorId, String sensorType, double temperature, double humidity) async {
    final url = Uri.parse('$baseUrl/sensor/add');
    final response = await http.post(
      url,
      headers: await _getHeaders(),
      body: json.encode({
        'sensor_id': sensorId,
        'sensor_type': sensorType,
        'temperature': temperature,
        'humidity': humidity,
      }),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  // ============ Security ============
  Future<Map<String, dynamic>> getSecuritySummary() async {
    final url = Uri.parse('$baseUrl/security/summary');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  Future<List<dynamic>> getSecurityEvents({String? severity, int limit = 10}) async {
    final url = Uri.parse('$baseUrl/security/events?limit=$limit${severity != null ? '&severity=$severity' : ''}');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  Future<List<dynamic>> getThreatAlerts({String? threatLevel, int limit = 10}) async {
    final url = Uri.parse('$baseUrl/security/alerts?limit=$limit${threatLevel != null ? '&threat_level=$threatLevel' : ''}');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  // ============ Devices ============
  Future<List<dynamic>> getDevices({String? status, String? deviceType}) async {
    String queryParams = '';
    if (status != null) queryParams += 'status=$status';
    if (deviceType != null) {
      queryParams += queryParams.isNotEmpty ? '&device_type=$deviceType' : 'device_type=$deviceType';
    }
    
    final url = Uri.parse('$baseUrl/devices/${queryParams.isNotEmpty ? '?$queryParams' : ''}');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  Future<Map<String, dynamic>> getDeviceHealthStatus() async {
    final url = Uri.parse('$baseUrl/devices/health/status');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  // ============ Users ============
  Future<List<dynamic>> getUsers() async {
    final url = Uri.parse('$baseUrl/users/');
    final response = await http.get(
      url,
      headers: await _getHeaders(),
    );

    _handleError(response);
    return json.decode(response.body);
  }

  // Get current user info (if available)
  // Note: This assumes you have a /users/me endpoint or similar
  // If not available, we'll decode the token to get user_id
  Future<Map<String, dynamic>?> getCurrentUser() async {
    // Try to get user info from token or API
    // For now, return null and we'll handle it in the UI
    try {
      final users = await getUsers();
      // This is a workaround - ideally backend should have /users/me endpoint
      // For now, we'll get the first user or handle it differently
      if (users.isNotEmpty) {
        return users[0] as Map<String, dynamic>;
      }
    } catch (e) {
      print('Error fetching user: $e');
    }
    return null;
  }
}

