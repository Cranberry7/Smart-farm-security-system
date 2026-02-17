import 'package:flutter/material.dart';
import 'SensorData.dart';
import 'UserProfilePage.dart';
import 'services/api_service.dart';
import 'services/token_storage.dart';
import 'main.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _apiService = ApiService();
  final _tokenStorage = TokenStorage();
  bool _isLoading = true;
  Map<String, dynamic>? _securitySummary;
  List<dynamic> _devices = [];
  List<dynamic> _recentAlerts = [];
  String _securityStatus = "Loading...";
  Color _securityStatusColor = Colors.grey;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      // Fetch security summary
      final summary = await _apiService.getSecuritySummary();
      
      // Fetch devices
      final devices = await _apiService.getDevices();
      
      // Fetch recent alerts (high/critical severity)
      final alerts = await _apiService.getThreatAlerts(threatLevel: 'high', limit: 5);

      setState(() {
        _securitySummary = summary;
        _devices = devices;
        _recentAlerts = alerts;
        _updateSecurityStatus();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _securityStatus = "Error loading data";
        _securityStatusColor = Colors.red;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading data: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  void _updateSecurityStatus() {
    if (_securitySummary != null) {
      final activeThreats = _securitySummary!['active_threats'] ?? 0;
      final criticalEvents = _securitySummary!['critical_events'] ?? 0;
      
      if (activeThreats == 0 && criticalEvents == 0) {
        _securityStatus = "All Systems Secure";
        _securityStatusColor = Colors.green;
      } else if (criticalEvents > 0) {
        _securityStatus = "$criticalEvents Critical Threat(s)";
        _securityStatusColor = Colors.red;
      } else {
        _securityStatus = "$activeThreats Active Threat(s)";
        _securityStatusColor = Colors.orange;
      }
    }
  }

  Future<void> _handleLogout() async {
    await _tokenStorage.deleteToken();
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const MyApp()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE3F2FD),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE3F2FD),
        elevation: 0,
        centerTitle: true,
        title: const Text(
          "Smart Farm Dashboard",
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Colors.redAccent,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline, color: Colors.redAccent, size: 28),
            tooltip: "View Profile",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const UserProfilePage()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.redAccent, size: 24),
            tooltip: "Logout",
            onPressed: _handleLogout,
          ),
          const SizedBox(width: 10),
        ],
      ),

      // Body
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Text(
                      "Welcome to Smart Farm",
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w600,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 30),

                    //  Uniform Action Cards Row
                    Wrap(
                      spacing: 20,
                      runSpacing: 20,
                      alignment: WrapAlignment.center,
                      children: [
                        _buildActionCard(
                          context,
                          icon: Icons.analytics_outlined,
                          title: "Device Analytics",
                          color: Colors.blueAccent,
                          destination: const SensorDataPage(),
                        ),
                        _buildActionCard(
                          context,
                          icon: Icons.settings_remote,
                          title: "Remote Control",
                          color: Colors.green,
                          destination: null,
                        ),
                      ],
                    ),
                    const SizedBox(height: 30),

                    // 🛡 Info Cards - uniform in height and width
                    _buildInfoCard(
                      title: "Security Status",
                      content: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Flexible(
                            child: Text(
                              _securityStatus,
                              style: const TextStyle(fontSize: 16, color: Colors.white),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Icon(
                            _securityStatusColor == Colors.green
                                ? Icons.check_circle
                                : Icons.warning,
                            color: _securityStatusColor,
                          ),
                        ],
                      ),
                    ),
                    _buildInfoCard(
                      title: "Connected Devices (${_devices.length})",
                      content: _devices.isEmpty
                          ? const Text(
                              "No devices registered",
                              style: TextStyle(color: Colors.white),
                            )
                          : Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: _devices.take(5).map((device) {
                                final deviceName = device['device_name'] ?? device['device_id'] ?? 'Unknown';
                                final status = device['status'] ?? 'unknown';
                                return Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 2),
                                  child: Row(
                                    children: [
                                      Icon(
                                        _getDeviceStatusIcon(status),
                                        color: _getDeviceStatusColor(status),
                                        size: 16,
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          "• $deviceName",
                                          style: const TextStyle(color: Colors.white),
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }).toList(),
                            ),
                    ),
                    _buildInfoCard(
                      title: "Recent Alerts (${_recentAlerts.length})",
                      content: _recentAlerts.isEmpty
                          ? const Text(
                              "No recent alerts.",
                              style: TextStyle(color: Colors.white),
                            )
                          : Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: _recentAlerts.take(3).map((alert) {
                                final description = alert['description'] ?? 'Alert';
                                final threatLevel = alert['threat_level'] ?? 'medium';
                                return Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 4),
                                  child: Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Icon(
                                        _getThreatIcon(threatLevel),
                                        color: _getThreatColor(threatLevel),
                                        size: 16,
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          description.length > 50
                                              ? "${description.substring(0, 50)}..."
                                              : description,
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 14,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              }).toList(),
                            ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  IconData _getDeviceStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return Icons.check_circle;
      case 'suspicious':
        return Icons.warning;
      case 'quarantined':
        return Icons.block;
      default:
        return Icons.help_outline;
    }
  }

  Color _getDeviceStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return Colors.green;
      case 'suspicious':
        return Colors.orange;
      case 'quarantined':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData _getThreatIcon(String threatLevel) {
    switch (threatLevel.toLowerCase()) {
      case 'critical':
        return Icons.dangerous;
      case 'high':
        return Icons.warning;
      default:
        return Icons.info;
    }
  }

  Color _getThreatColor(String threatLevel) {
    switch (threatLevel.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      default:
        return Colors.yellow;
    }
  }

  //  Uniform Feature Card
  Widget _buildActionCard(BuildContext context,
      {required IconData icon,
        required String title,
        required Color color,
        Widget? destination}) {
    return GestureDetector(
      onTap: destination != null
          ? () => Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => destination),
      )
          : null,
      child: Container(
        width: 150, // uniform width
        height: 150, // uniform height
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(20),
          boxShadow: const [
            BoxShadow(
              color: Colors.black26,
              blurRadius: 5,
              offset: const Offset(2, 3),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 40),
            const SizedBox(height: 10),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  //  Uniform Info Card
  Widget _buildInfoCard({required String title, required Widget content}) {
    return Card(
      color: Colors.blue[400],
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
      ),
      margin: const EdgeInsets.symmetric(vertical: 10),
      child: SizedBox(
        width: double.infinity,
        height: 125, // uniform height for info cards
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 10),
              content,
            ],
          ),
        ),
      ),
    );
  }
}
