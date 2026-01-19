import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/file_analysis.dart';
import '../models/password_validation.dart';

class ApiService {
  final Dio _dio;

  ApiService()
      : _dio = Dio(
    BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: ApiConfig.connectionTimeout,
      receiveTimeout: ApiConfig.receiveTimeout,
      headers: {
        'Accept': 'application/json',
      },
    ),
  );

  // Analyze file and get metadata (supports both mobile and web)
  Future<FileAnalysis> analyzeFile(
      dynamic file, // Can be File or Uint8List with filename
      String fileName, {
        String platform = 'general',
      }) async {
    try {
      MultipartFile multipartFile;

      if (file is File) {
        // Mobile: use File
        multipartFile = await MultipartFile.fromFile(
          file.path,
          filename: fileName,
        );
      } else if (file is Uint8List) {
        // Web: use bytes
        multipartFile = MultipartFile.fromBytes(
          file,
          filename: fileName,
        );
      } else {
        throw Exception('Unsupported file type');
      }

      final formData = FormData.fromMap({
        'file': multipartFile,
        'platform': platform,
      });

      final response = await _dio.post(
        ApiConfig.analyze,
        data: formData,
        options: Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      return FileAnalysis.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Clean file and download
  Future<Uint8List> cleanAndDownload(dynamic file, String fileName) async {
    try {
      MultipartFile multipartFile;

      if (file is File) {
        multipartFile = await MultipartFile.fromFile(file.path, filename: fileName);
      } else if (file is Uint8List) {
        multipartFile = MultipartFile.fromBytes(file, filename: fileName);
      } else {
        throw Exception('Unsupported file type');
      }

      final formData = FormData.fromMap({
        'file': multipartFile,
      });

      final response = await _dio.post(
        ApiConfig.cleanDownload,
        data: formData,
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      return Uint8List.fromList(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Download cleaned file by analysis ID
  Future<Uint8List> downloadCleanedFile(String analysisId) async {
    try {
      final response = await _dio.post(
        ApiConfig.clean,
        data: {'analysis_id': analysisId},
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      return Uint8List.fromList(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Encrypt file
  Future<Uint8List> encryptFile(
      dynamic file,
      String fileName,
      String password,
      String method,
      ) async {
    try {
      MultipartFile multipartFile;

      if (file is File) {
        multipartFile = await MultipartFile.fromFile(file.path, filename: fileName);
      } else if (file is Uint8List) {
        multipartFile = MultipartFile.fromBytes(file, filename: fileName);
      } else {
        throw Exception('Unsupported file type');
      }

      final formData = FormData.fromMap({
        'file': multipartFile,
        'password': password,
        'method': method,
      });

      final response = await _dio.post(
        ApiConfig.encrypt,
        data: formData,
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      return Uint8List.fromList(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Decrypt file
  Future<Uint8List> decryptFile(
      dynamic file,
      String fileName,
      String password, {
        String? originalFilename,
      }) async {
    try {
      MultipartFile multipartFile;

      if (file is File) {
        multipartFile = await MultipartFile.fromFile(file.path, filename: fileName);
      } else if (file is Uint8List) {
        multipartFile = MultipartFile.fromBytes(file, filename: fileName);
      } else {
        throw Exception('Unsupported file type');
      }

      final formData = FormData.fromMap({
        'file': multipartFile,
        'password': password,
        if (originalFilename != null) 'original_filename': originalFilename,
      });

      final response = await _dio.post(
        ApiConfig.decrypt,
        data: formData,
        options: Options(
          responseType: ResponseType.bytes,
        ),
      );

      return Uint8List.fromList(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Validate password strength
  Future<PasswordValidation> validatePassword(String password) async {
    try {
      final response = await _dio.post(
        ApiConfig.validatePassword,
        data: {'password': password},
      );

      return PasswordValidation.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Get analysis history
  Future<List<FileAnalysis>> getAnalysisHistory() async {
    try {
      final response = await _dio.get(ApiConfig.analyses);

      final List<dynamic> data = response.data['results'] ?? response.data;
      return data.map((json) => FileAnalysis.fromJson(json)).toList();
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Get shared file info
  Future<FileAnalysis> getSharedFile(String shareToken) async {
    try {
      final response = await _dio.get('${ApiConfig.share}$shareToken/');
      return FileAnalysis.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Check API health
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get(ApiConfig.health);
      return response.data['status'] == 'healthy';
    } catch (e) {
      return false;
    }
  }

  // Error handling
  String _handleError(DioException e) {
    print('DioException Type: ${e.type}');
    print('DioException Message: ${e.message}');
    print('DioException Response: ${e.response?.data}');

    if (e.response != null) {
      final data = e.response?.data;
      if (data is Map && data.containsKey('error')) {
        return data['error'];
      }
      if (data is Map && data.containsKey('file')) {
        return data['file'].toString();
      }
      if (data is String) {
        return data;
      }
      return 'Server error: ${e.response?.statusCode} - ${e.response?.statusMessage}';
    } else if (e.type == DioExceptionType.connectionTimeout) {
      return 'Connection timeout. Please check your internet connection.';
    } else if (e.type == DioExceptionType.receiveTimeout) {
      return 'Server is taking too long to respond.';
    } else {
      return 'Network error: ${e.message}';
    }
  }
}