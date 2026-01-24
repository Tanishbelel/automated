class ApiConfig {
  // Change this to your Django backend URL
  static const String baseUrl = 'http://10.197.86.80:8000/api';// For Android Emulator
  // static const String baseUrl = 'http://localhost:8000/api'; // For iOS Simulator
  // static const String baseUrl = 'https://your-domain.com/api'; // For production

  // Endpoints
  static const String register = '/auth/register/';
  static const String login = '/auth/login/';
  static const String logout = '/auth/logout/';
  static const String profile = '/auth/profile/';
  static const String profileUpdate = '/auth/profile/update/';
  static const String changePassword = '/auth/change-password/';
  static const String deleteAccount = '/auth/delete-account/';


  static const String analyze = '/analyze/';
  static const String clean = '/clean/';
  static const String cleanDownload = '/clean-download/';
  static const String encrypt = '/encrypt/';
  static const String decrypt = '/decrypt/';
  static const String validatePassword = '/validate-password/';
  static const String analyses = '/analyses/';
  static const String share = '/share/';
  static const String makePublic = '/make-public/';
  static const String health = '/health/';

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);

  // Build full URL
  static String getUrl(String endpoint) => baseUrl + endpoint;
}