import 'package:flutter/material.dart';
import 'dart:async';
import '../services/api_service.dart';
import 'login_screen.dart';
import 'home_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();

    // Setup animations
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutBack),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );

    _controller.forward();

    // Check authentication and navigate
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Wait for animation to complete
    await Future.delayed(const Duration(milliseconds: 2000));

    if (!mounted) return;

    // Check if user is authenticated
    final apiService = ApiService();
    final isAuthenticated = await apiService.isAuthenticated();

    if (!mounted) return;

    // Navigate to appropriate screen
    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
        isAuthenticated ? const HomeScreen() : const LoginScreen(),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
        transitionDuration: const Duration(milliseconds: 500),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Animated Logo
            ScaleTransition(
              scale: _scaleAnimation,
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: Container(
                  padding: const EdgeInsets.all(36),
                  decoration: const BoxDecoration(
                    color: Color(0xFF3182CE),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.shield_rounded,
                    size: 72,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 40),

            // App Name
            FadeTransition(
              opacity: _fadeAnimation,
              child: const Text(
                'Metadata Remover',
                style: TextStyle(
                  color: Color(0xFF2D3748),
                  fontSize: 30,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.5,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Tagline
            FadeTransition(
              opacity: _fadeAnimation,
              child: const Text(
                'Protect Your Privacy',
                style: TextStyle(
                  color: Color(0xFF718096),
                  fontSize: 16,
                  letterSpacing: 0.3,
                ),
              ),
            ),
            const SizedBox(height: 60),

            // Loading Indicator
            FadeTransition(
              opacity: _fadeAnimation,
              child: const SizedBox(
                width: 36,
                height: 36,
                child: CircularProgressIndicator(
                  strokeWidth: 3,
                  valueColor:
                  AlwaysStoppedAnimation<Color>(Color(0xFF3182CE)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}