import 'package:flutter/material.dart';
import 'HomePage.dart';
import 'services/api_service.dart';
import 'services/token_storage.dart';

void main() {
  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: MyApp(),
  ));
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailController = TextEditingController();
  final _apiService = ApiService();
  final _tokenStorage = TokenStorage();
  bool _isLoading = false;
  bool _isLogin = true;
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    _checkLoginStatus();
  }

  Future<void> _checkLoginStatus() async {
    final isLoggedIn = await _tokenStorage.isLoggedIn();
    if (isLoggedIn && mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomePage()),
      );
    }
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      await _apiService.login(
        _usernameController.text.trim(),
        _passwordController.text,
      );

      // Save username for profile (email might not be available during login)
      await _tokenStorage.saveUserInfo(
        _usernameController.text.trim(),
        _emailController.text.trim().isNotEmpty 
            ? _emailController.text.trim() 
            : '${_usernameController.text.trim()}@smartfarm.com',
      );

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomePage()),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Login failed: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      await _apiService.register(
        _usernameController.text.trim(),
        _emailController.text.trim(),
        _passwordController.text,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Registration successful! Please login.'),
            backgroundColor: Colors.green,
          ),
        );
        setState(() => _isLogin = true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Registration failed: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE3F2FD),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // --- App Logo and Title ---
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Image(
                          height: 75,
                          width: 75,
                          image: AssetImage('images/logo.jpg'),
                        ),
                        const SizedBox(width: 10),
                        RichText(
                          text: const TextSpan(
                            children: [
                              TextSpan(
                                text: "Byte",
                                style: TextStyle(
                                  fontSize: 44,
                                  color: Color(0xff203142),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              TextSpan(
                                text: "Field",
                                style: TextStyle(
                                  fontSize: 44,
                                  color: Colors.redAccent,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 40),

                    // --- Welcome Message ---
                    Text(
                      _isLogin
                          ? "Welcome to our app\nA threat-free environment!"
                          : "Create your account\nJoin Smart Farm Security!",
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 18,
                        color: Color(0xff4C5980),
                        fontWeight: FontWeight.w500,
                        height: 1.5,
                      ),
                    ),

                    const SizedBox(height: 50),

                    // --- Username Field ---
                    TextFormField(
                      controller: _usernameController,
                      decoration: const InputDecoration(
                        labelText: "Username",
                        hintText: "Enter your username",
                        fillColor: Color(0xffF8F9FA),
                        filled: true,
                        prefixIcon: Icon(Icons.person_outline),
                        enabledBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: Color(0xffE4E7EB)),
                          borderRadius: BorderRadius.all(Radius.circular(10)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: Colors.redAccent),
                          borderRadius: BorderRadius.all(Radius.circular(10)),
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your username';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 20),

                    // --- Email Field (for registration) ---
                    if (!_isLogin) ...[
                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(
                          labelText: "E-Mail",
                          hintText: "Enter your email",
                          fillColor: Color(0xffF8F9FA),
                          filled: true,
                          prefixIcon: Icon(Icons.email_outlined),
                          enabledBorder: OutlineInputBorder(
                            borderSide: BorderSide(color: Color(0xffE4E7EB)),
                            borderRadius: BorderRadius.all(Radius.circular(10)),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderSide: BorderSide(color: Colors.redAccent),
                            borderRadius: BorderRadius.all(Radius.circular(10)),
                          ),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your email';
                          }
                          if (!value.contains('@')) {
                            return 'Please enter a valid email';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                    ],

                    // --- Password Field ---
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      decoration: InputDecoration(
                        labelText: "Password",
                        hintText: "Enter your password",
                        fillColor: const Color(0xffF8F9FA),
                        filled: true,
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                          ),
                          onPressed: () {
                            setState(() => _obscurePassword = !_obscurePassword);
                          },
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderSide: const BorderSide(color: Color(0xffE4E7EB)),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderSide: const BorderSide(
                              color: Colors.redAccent, width: 1.2),
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter your password';
                        }
                        if (value.length < 6) {
                          return 'Password must be at least 6 characters';
                        }
                        return null;
                      },
                    ),

                    const SizedBox(height: 60),

                    // --- Login/Register Button ---
                    SizedBox(
                      width: 250,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _isLoading
                            ? null
                            : (_isLogin ? _handleLogin : _handleRegister),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.redAccent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          elevation: 3,
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor:
                                      AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              )
                            : Text(
                                _isLogin ? "Login" : "Register",
                                style: const TextStyle(
                                  fontSize: 18,
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                      ),
                    ),

                    const SizedBox(height: 20),

                    // --- Sign Up/Login Text ---
                    GestureDetector(
                      onTap: () {
                        setState(() {
                          _isLogin = !_isLogin;
                          _formKey.currentState?.reset();
                        });
                      },
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _isLogin
                                ? "Don't have an account? "
                                : "Already have an account? ",
                            style: const TextStyle(
                              fontSize: 16,
                              color: Colors.black87,
                            ),
                          ),
                          const Text(
                            "Sign Up",
                            style: TextStyle(
                              fontSize: 16,
                              color: Colors.redAccent,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
