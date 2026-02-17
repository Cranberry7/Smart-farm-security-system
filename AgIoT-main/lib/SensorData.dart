import 'package:flutter/material.dart';
import 'HomePage.dart';
import 'services/api_service.dart';

class SensorDataPage extends StatefulWidget {
  const SensorDataPage({super.key});

  @override
  State<SensorDataPage> createState() => _SensorDataPageState();
}

class _SensorDataPageState extends State<SensorDataPage> {
  final _apiService = ApiService();
  bool _isLoading = true;
  List<dynamic> _sensorData = [];
  Map<String, dynamic> _latestReadings = {};

  @override
  void initState() {
    super.initState();
    _loadSensorData();
  }

  Future<void> _loadSensorData() async {
    setState(() => _isLoading = true);

    try {
      final data = await _apiService.getSensorData();
      
      // Process data to get latest readings per sensor
      Map<String, dynamic> latest = {};
      for (var reading in data) {
        final sensorId = reading['sensor_id'] ?? 'unknown';
        final timestamp = reading['timestamp'] != null 
            ? DateTime.parse(reading['timestamp'])
            : null;
        
        if (!latest.containsKey(sensorId) || 
            (timestamp != null && 
             latest[sensorId]['timestamp'] != null &&
             timestamp.isAfter(DateTime.parse(latest[sensorId]['timestamp'])))) {
          latest[sensorId] = reading;
        }
      }

      setState(() {
        _sensorData = data;
        _latestReadings = latest;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading sensor data: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  String _formatTimestamp(String? timestamp) {
    if (timestamp == null) return 'N/A';
    try {
      final dt = DateTime.parse(timestamp);
      final now = DateTime.now();
      final diff = now.difference(dt);
      
      if (diff.inMinutes < 1) {
        return 'Just now';
      } else if (diff.inHours < 1) {
        return '${diff.inMinutes}m ago';
      } else if (diff.inDays < 1) {
        return '${diff.inHours}h ago';
      } else {
        return '${diff.inDays}d ago';
      }
    } catch (e) {
      return 'N/A';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE3F2FD),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE3F2FD),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.redAccent),
          onPressed: () {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => const HomePage()),
            );
          },
        ),
        title: const Text(
          "Farm Sensor Data",
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: Colors.redAccent,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.redAccent),
            onPressed: _loadSensorData,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadSensorData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _latestReadings.isEmpty
                ? const Center(
                    child: Text(
                      "No sensor data available",
                      style: TextStyle(fontSize: 16, color: Colors.black87),
                    ),
                  )
                : ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      // Display latest readings grouped by sensor
                      ..._latestReadings.entries.map((entry) {
                        final sensorId = entry.key;
                        final reading = entry.value;
                        final temp = reading['temperature'];
                        final humidity = reading['humidity'];
                        final timestamp = reading['timestamp'];
                        
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            if (temp != null)
                              _buildSensorCard(
                                "Temperature (${sensorId})",
                                "${temp.toStringAsFixed(1)} °C",
                                Icons.thermostat,
                                _formatTimestamp(timestamp),
                              ),
                            if (humidity != null)
                              _buildSensorCard(
                                "Humidity (${sensorId})",
                                "${humidity.toStringAsFixed(1)} %",
                                Icons.water_drop,
                                _formatTimestamp(timestamp),
                              ),
                            if (temp == null && humidity == null)
                              _buildSensorCard(
                                "Sensor: $sensorId",
                                "No data available",
                                Icons.sensors,
                                _formatTimestamp(timestamp),
                              ),
                            const SizedBox(height: 10),
                          ],
                        );
                      }).toList(),
                      
                      // Summary card
                      Card(
                        color: Colors.blue[300],
                        margin: const EdgeInsets.only(top: 20),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                "Summary",
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                "Total Readings: ${_sensorData.length}",
                                style: const TextStyle(color: Colors.white),
                              ),
                              Text(
                                "Active Sensors: ${_latestReadings.length}",
                                style: const TextStyle(color: Colors.white),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
      ),
    );
  }

  // Reusable Sensor Card
  Widget _buildSensorCard(
      String title, String value, IconData icon, String timestamp) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      color: Colors.blue[400],
      child: ListTile(
        leading: Icon(icon, color: Colors.white, size: 32),
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
        subtitle: Text(
          timestamp,
          style: const TextStyle(fontSize: 12, color: Colors.white70),
        ),
        trailing: Text(
          value,
          style: const TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}
