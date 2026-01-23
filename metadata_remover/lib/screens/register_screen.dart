import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _password2Controller = TextEditingController();
  final TextEditingController _firstNameController = TextEditingController();
  final TextEditingController _lastNameController = TextEditingController();

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscurePassword2 = true;
  String? _errorMessage;

  @override
  void dispose() {
    _usernameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _password2Controller.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 440),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: const BoxDecoration(
                          color: Color(0xFF3182CE),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.person_add_rounded,
                          size: 48,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 24),
                      const Text(
                        'Create Account',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF2D3748),
                          fontSize: 26,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Join us to protect your privacy',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color(0xFF718096),
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 32),
                      if (_errorMessage != null) ...[
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFF5F5),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: const Color(0xFFE53E3E).withOpacity(0.3),
                            ),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline,
                                  color: Color(0xFFE53E3E), size: 20),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(
                                    color: Color(0xFFE53E3E),
                                    fontSize: 14,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],
                      _buildTextField(
                        controller: _usernameController,
                        label: 'Username',
                        icon: Icons.person_rounded,
                      ),
                      const SizedBox(height: 16),
                      _buildTextField(
                        controller: _emailController,
                        label: 'Email',
                        icon: Icons.email_rounded,
                        keyboardType: TextInputType.emailAddress,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTextField(
                              controller: _firstNameController,
                              label: 'First Name',
                              icon: Icons.badge_rounded,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _buildTextField(
                              controller: _lastNameController,
                              label: 'Last Name',
                              icon: Icons.badge_rounded,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      _buildTextField(
                        controller: _passwordController,
                        label: 'Password',
                        icon: Icons.lock_rounded,
                        obscureText: _obscurePassword,
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_rounded
                                : Icons.visibility_off_rounded,
                            color: const Color(0xFF718096),
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                      ),
                      const SizedBox(height: 16),
                      _buildTextField(
                        controller: _password2Controller,
                        label: 'Confirm Password',
                        icon: Icons.lock_rounded,
                        obscureText: _obscurePassword2,
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword2
                                ? Icons.visibility_rounded
                                : Icons.visibility_off_rounded,
                            color: const Color(0xFF718096),
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword2 = !_obscurePassword2;
                            });
                          },
                        ),
                      ),
                      const SizedBox(height: 28),
                      _buildRegisterButton(),
                      const SizedBox(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            'Already have an account? ',
                            style: TextStyle(
                              color: Color(0xFF718096),
                              fontSize: 14,
                            ),
                          ),
                          GestureDetector(
                            onTap: () {
                              Navigator.pop(context);
                            },
                            child: const Text(
                              'Sign In',
                              style: TextStyle(
                                color: Color(0xFF3182CE),
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          bottom: BorderSide(color: const Color(0xFFE2E8F0), width: 1),
        ),
      ),
      child: Row(
        children: [
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFFF7FAFC),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
            ),
            child: IconButton(
              icon: const Icon(Icons.arrow_back_rounded,
                  color: Color(0xFF4A5568)),
              onPressed: () => Navigator.pop(context),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool obscureText = false,
    Widget? suffixIcon,
    TextInputType? keyboardType,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color(0xFFE2E8F0),
          width: 1,
        ),
      ),
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        style: const TextStyle(color: Color(0xFF2D3748)),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Color(0xFF718096)),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
          prefixIcon: Icon(icon, color: const Color(0xFF3182CE)),
          suffixIcon: suffixIcon,
        ),
      ),
    );
  }

  Widget _buildRegisterButton() {
    return SizedBox(
      width: double.infinity,
      child: Container(
        decoration: BoxDecoration(
          color: _isLoading
              ? const Color(0xFFE2E8F0)
              : const Color(0xFF3182CE),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: _isLoading ? null : _handleRegister,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_isLoading)
                    SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          _isLoading
                              ? const Color(0xFF718096)
                              : Colors.white,
                        ),
                      ),
                    )
                  else
                    const Icon(Icons.person_add_rounded,
                        color: Colors.white, size: 22),
                  const SizedBox(width: 12),
                  Text(
                    _isLoading ? 'Creating Account...' : 'Create Account',
                    style: TextStyle(
                      color: _isLoading
                          ? const Color(0xFF718096)
                          : Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _handleRegister() async {
    final username = _usernameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final password2 = _password2Controller.text;
    final firstName = _firstNameController.text.trim();
    final lastName = _lastNameController.text.trim();

    if (username.isEmpty ||
        email.isEmpty ||
        password.isEmpty ||
        password2.isEmpty) {
      setState(() {
        _errorMessage = 'Please fill in all required fields';
      });
      return;
    }

    if (password != password2) {
      setState(() {
        _errorMessage = 'Passwords do not match';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await _apiService.register(
        username: username,
        email: email,
        password: password,
        password2: password2,
        firstName: firstName.isEmpty ? null : firstName,
        lastName: lastName.isEmpty ? null : lastName,
      );

      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Account created successfully!'),
          backgroundColor: const Color(0xFF38A169),
          behavior: SnackBarBehavior.floating,
          shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
      );
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
}