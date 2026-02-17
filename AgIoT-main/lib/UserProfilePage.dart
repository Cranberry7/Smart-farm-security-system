import 'package:flutter/material.dart';
import 'HomePage.dart';
import 'services/token_storage.dart';
import 'services/api_service.dart';

class UserProfilePage extends StatefulWidget {
  const UserProfilePage({super.key});

  @override
  State<UserProfilePage> createState() => _UserProfilePageState();
}

class _UserProfilePageState extends State<UserProfilePage> {
  final _tokenStorage = TokenStorage();
  final _apiService = ApiService();
  bool _isLoading = true;
  String? _username;
  String? _email;
  Map<String, dynamic>? _userData;

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    setState(() => _isLoading = true);

    try {
      // Get saved username and email
      final username = await _tokenStorage.getUsername();
      final email = await _tokenStorage.getEmail();
      
      // Try to get user data from API
      Map<String, dynamic>? userData;
      try {
        userData = await _apiService.getCurrentUser();
      } catch (e) {
        // If API fails, use stored data
        print('Could not fetch user from API: $e');
      }

      setState(() {
        _username = username ?? userData?['username'] ?? 'User';
        _email = email ?? userData?['email'] ?? 'No email';
        _userData = userData;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading profile: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
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
          "User Profile",
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: Colors.redAccent,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const CircleAvatar(
                    radius: 60,
                    backgroundColor: Colors.redAccent,
                    child: Icon(
                      Icons.person,
                      size: 60,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    _username ?? "User",
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.redAccent,
                    ),
                  ),
                  const SizedBox(height: 5),
                  const Text(
                    "Farmer",
                    style: TextStyle(fontSize: 16, color: Colors.black87),
                  ),
                  const SizedBox(height: 30),

                  // Profile info card
                  _buildInfoCard("Email", _email ?? "No email available"),
                  if (_userData != null && _userData!['id'] != null)
                    _buildInfoCard("User ID", "#${_userData!['id']}"),
                  if (_userData != null && _userData!['created_at'] != null)
                    _buildInfoCard(
                      "Member Since",
                      _formatDate(_userData!['created_at']),
                    ),
                  _buildInfoCard("Role", "Farm Administrator"),

                  const Spacer(),
                  SizedBox(
                    width: 200,
                    child: ElevatedButton(
                      onPressed: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Edit profile coming soon!"),
                          ),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent,
                        padding: const EdgeInsets.symmetric(vertical: 15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      child: const Text(
                        "Edit Profile",
                        style: TextStyle(fontSize: 16, color: Colors.white),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  String _formatDate(String? dateString) {
    if (dateString == null) return 'N/A';
    try {
      final date = DateTime.parse(dateString);
      return '${date.day}/${date.month}/${date.year}';
    } catch (e) {
      return dateString;
    }
  }

  Widget _buildInfoCard(String label, String value) {
    return Card(
      color: Colors.blue[400],
      margin: const EdgeInsets.symmetric(vertical: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.info_outline, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 16,
                      color: Colors.white70,
                    ),
                    softWrap: true,
                    overflow: TextOverflow.visible,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

}
