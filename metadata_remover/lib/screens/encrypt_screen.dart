import 'dart:typed_data';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';

import '../utils/mobile_download.dart';
import '../services/api_service.dart';
import '../models/password_validation.dart';

class EncryptScreen extends StatefulWidget {
  const EncryptScreen({super.key});

  @override
  State<EncryptScreen> createState() => _EncryptScreenState();
}

class _EncryptScreenState extends State<EncryptScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _passwordController = TextEditingController();
  bool _isProcessing = false;
  bool _isEncryptMode = true;
  Uint8List? _selectedFileBytes;
  File? _selectedFile; // Add this for mobile
  String? _selectedFileName;
  String _encryptionMethod = 'encrypt';
  PasswordValidation? _passwordValidation;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildModeSelector(),
          const SizedBox(height: 16),
          _buildInfoCard(),
          const SizedBox(height: 16),
          _buildFileSelection(),
          const SizedBox(height: 16),
          if (_isEncryptMode) ...[
            _buildEncryptionMethodSelector(),
            const SizedBox(height: 16),
          ],
          _buildPasswordField(),
          const SizedBox(height: 12),
          if (_isEncryptMode && _passwordValidation != null) ...[
            _buildPasswordStrengthIndicator(),
            const SizedBox(height: 16),
          ],
          _buildProcessButton(),
        ],
      ),
    );
  }

  Widget _buildModeSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildModeButton(
              isSelected: _isEncryptMode,
              icon: Icons.lock_rounded,
              label: 'Encrypt',
              onTap: () {
                setState(() {
                  _isEncryptMode = true;
                  _resetForm();
                });
              },
            ),
          ),
          Expanded(
            child: _buildModeButton(
              isSelected: !_isEncryptMode,
              icon: Icons.lock_open_rounded,
              label: 'Decrypt',
              onTap: () {
                setState(() {
                  _isEncryptMode = false;
                  _resetForm();
                });
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildModeButton({
    required bool isSelected,
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF3182CE) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.white : const Color(0xFF718096),
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF718096),
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                fontSize: 15,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _isEncryptMode
            ? const Color(0xFFEBF8FF)
            : const Color(0xFFF0FFF4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _isEncryptMode
              ? const Color(0xFF3182CE).withOpacity(0.2)
              : const Color(0xFF38A169).withOpacity(0.2),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _isEncryptMode
                  ? const Color(0xFF3182CE)
                  : const Color(0xFF38A169),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              _isEncryptMode ? Icons.shield_rounded : Icons.vpn_key_rounded,
              color: Colors.white,
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isEncryptMode
                      ? 'Password Protect Your Files'
                      : 'Unlock Protected Files',
                  style: const TextStyle(
                    color: Color(0xFF2D3748),
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _isEncryptMode
                      ? 'Add an extra layer of security with encryption.'
                      : 'Enter password to decrypt your files.',
                  style: const TextStyle(
                    color: Color(0xFF718096),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFileSelection() {
    if (_selectedFileName == null) {
      return GestureDetector(
        onTap: _pickFile,
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: const Color(0xFFCBD5E0),
              width: 2,
              style: BorderStyle.solid,
            ),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: const BoxDecoration(
                  color: Color(0xFFF7FAFC),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.cloud_upload_rounded,
                  color: Color(0xFF3182CE),
                  size: 36,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Select File',
                style: TextStyle(
                  color: Color(0xFF2D3748),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Tap to choose a file',
                style: TextStyle(
                  color: Color(0xFF718096),
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFFEBF8FF),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.insert_drive_file_rounded,
              color: Color(0xFF3182CE),
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _selectedFileName!,
              style: const TextStyle(
                color: Color(0xFF2D3748),
                fontWeight: FontWeight.w500,
                fontSize: 14,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded, color: Color(0xFF718096)),
            onPressed: () {
              setState(() {
                _selectedFileBytes = null;
                _selectedFile = null;
                _selectedFileName = null;
              });
            },
          ),
        ],
      ),
    );
  }

  Widget _buildEncryptionMethodSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Encryption Method',
          style: TextStyle(
            color: Color(0xFF2D3748),
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
          ),
          child: Row(
            children: [
              Expanded(
                child: _buildMethodButton(
                  isSelected: _encryptionMethod == 'encrypt',
                  label: 'Standard',
                  onTap: () => setState(() => _encryptionMethod = 'encrypt'),
                ),
              ),
              Expanded(
                child: _buildMethodButton(
                  isSelected: _encryptionMethod == 'zip',
                  label: 'ZIP',
                  onTap: () => setState(() => _encryptionMethod = 'zip'),
                ),
              ),
              Expanded(
                child: _buildMethodButton(
                  isSelected: _encryptionMethod == 'pdf',
                  label: 'PDF',
                  onTap: () => setState(() => _encryptionMethod = 'pdf'),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMethodButton({
    required bool isSelected,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF3182CE) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? Colors.white : const Color(0xFF718096),
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              fontSize: 14,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPasswordField() {
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
        controller: _passwordController,
        obscureText: _obscurePassword,
        style: const TextStyle(color: Color(0xFF2D3748)),
        decoration: InputDecoration(
          labelText: 'Password',
          labelStyle: const TextStyle(color: Color(0xFF718096)),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
          prefixIcon: const Icon(Icons.lock_rounded, color: Color(0xFF3182CE)),
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
        onChanged: _isEncryptMode ? _validatePassword : null,
      ),
    );
  }

  Widget _buildPasswordStrengthIndicator() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Password Strength',
                style: TextStyle(
                  color: Color(0xFF4A5568),
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                '${_passwordValidation!.score}/100',
                style: TextStyle(
                  color: _getPasswordStrengthColor(_passwordValidation!.strength),
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: _passwordValidation!.score / 100,
              backgroundColor: const Color(0xFFF7FAFC),
              color: _getPasswordStrengthColor(_passwordValidation!.strength),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getPasswordStrengthColor(_passwordValidation!.strength)
                  .withOpacity(0.1),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: _getPasswordStrengthColor(_passwordValidation!.strength)
                    .withOpacity(0.3),
                width: 1,
              ),
            ),
            child: Text(
              _passwordValidation!.strength.toUpperCase(),
              style: TextStyle(
                color: _getPasswordStrengthColor(_passwordValidation!.strength),
                fontWeight: FontWeight.w600,
                fontSize: 11,
              ),
            ),
          ),
          if (_passwordValidation!.feedback.isNotEmpty) ...[
            const SizedBox(height: 12),
            ..._passwordValidation!.feedback.map((feedback) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.info_outline_rounded,
                    size: 16,
                    color: Color(0xFF718096),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      feedback,
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF4A5568),
                      ),
                    ),
                  ),
                ],
              ),
            )).toList(),
          ],
        ],
      ),
    );
  }

  Widget _buildProcessButton() {
    final isEnabled = (_selectedFileBytes != null || _selectedFile != null) &&
        _passwordController.text.isNotEmpty &&
        !_isProcessing;

    return Container(
      decoration: BoxDecoration(
        color: isEnabled ? const Color(0xFF3182CE) : const Color(0xFFE2E8F0),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isEnabled ? _processFile : null,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (_isProcessing)
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        isEnabled ? Colors.white : const Color(0xFF718096),
                      ),
                    ),
                  )
                else
                  Icon(
                    _isEncryptMode
                        ? Icons.lock_rounded
                        : Icons.lock_open_rounded,
                    color: isEnabled ? Colors.white : const Color(0xFF718096),
                    size: 22,
                  ),
                const SizedBox(width: 12),
                Text(
                  _isProcessing
                      ? 'Processing...'
                      : _isEncryptMode
                      ? 'Encrypt File'
                      : 'Decrypt File',
                  style: TextStyle(
                    color: isEnabled ? Colors.white : const Color(0xFF718096),
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles();

      if (result != null && result.files.single.path != null) {
        // Mobile platform - use File
        if (!kIsWeb) {
          final file = File(result.files.single.path!);
          setState(() {
            _selectedFile = file;
            _selectedFileBytes = null;
            _selectedFileName = result.files.single.name;
          });

          if (kDebugMode) {
            print('File selected (Mobile): $_selectedFileName');
          }
        }
      } else if (result != null && result.files.single.bytes != null) {
        // Web platform - use bytes
        setState(() {
          _selectedFileBytes = result.files.single.bytes;
          _selectedFile = null;
          _selectedFileName = result.files.single.name;
        });

        if (kDebugMode) {
          print('File selected (Web): $_selectedFileName');
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('File picker error: $e');
      }
      _showErrorSnackBar('Failed to select file: $e');
    }
  }

  Future<void> _validatePassword(String password) async {
    if (password.isEmpty) {
      setState(() {
        _passwordValidation = null;
      });
      return;
    }

    try {
      final validation = await _apiService.validatePassword(password);
      if (mounted) {
        setState(() {
          _passwordValidation = validation;
        });
      }
    } catch (e) {
      if (kDebugMode) {
        print('Password validation error: $e');
      }
    }
  }

  Future<void> _processFile() async {
    if ((_selectedFileBytes == null && _selectedFile == null) || _passwordController.text.isEmpty) {
      _showErrorSnackBar('Please select a file and enter a password');
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    try {
      Uint8List resultBytes;
      String downloadFileName;

      // Determine which file type to use
      final fileToProcess = _selectedFile ?? _selectedFileBytes!;

      if (_isEncryptMode) {
        // Encrypt
        if (kDebugMode) {
          print('Encrypting file: $_selectedFileName with method: $_encryptionMethod');
        }

        resultBytes = await _apiService.encryptFile(
          fileToProcess,
          _selectedFileName!,
          _passwordController.text,
          _encryptionMethod,
        );

        final extension = _encryptionMethod == 'zip'
            ? 'zip'
            : _encryptionMethod == 'pdf'
            ? 'pdf'
            : 'enc';

        final baseName = _selectedFileName!.contains('.')
            ? _selectedFileName!.substring(0, _selectedFileName!.lastIndexOf('.'))
            : _selectedFileName!;

        downloadFileName = '${baseName}_protected.$extension';

        // Mobile download
        await downloadMobile(resultBytes, downloadFileName);

        if (!mounted) return;

        _showSuccessSnackBar('File encrypted and downloaded successfully!');
      } else {
        // Decrypt
        if (kDebugMode) {
          print('Decrypting file: $_selectedFileName');
        }

        resultBytes = await _apiService.decryptFile(
          fileToProcess,
          _selectedFileName!,
          _passwordController.text,
          originalFilename: _selectedFileName,
        );

        // Determine original filename
        String baseName = _selectedFileName!;
        if (baseName.endsWith('_protected.zip')) {
          baseName = baseName.replaceAll('_protected.zip', '');
        } else if (baseName.endsWith('_protected.enc')) {
          baseName = baseName.replaceAll('_protected.enc', '');
        } else if (baseName.endsWith('_protected.pdf')) {
          baseName = baseName.replaceAll('_protected.pdf', '.pdf');
        } else if (baseName.endsWith('.enc')) {
          baseName = baseName.replaceAll('.enc', '');
        }

        downloadFileName = baseName.contains('_decrypted')
            ? baseName
            : '${baseName}_decrypted';

        // Mobile download
        await downloadMobile(resultBytes, downloadFileName);

        if (!mounted) return;

        _showSuccessSnackBar('File decrypted and downloaded successfully!');
      }

      // Reset form
      _resetForm();
    } catch (e) {
      if (!mounted) return;

      if (kDebugMode) {
        print('Process error: $e');
      }

      String errorMessage = 'Process failed';
      String errorStr = e.toString().toLowerCase();

      if (errorStr.contains('wrong password') ||
          errorStr.contains('decryption failed') ||
          errorStr.contains('401')) {
        errorMessage = 'Wrong password or corrupted file';
      } else if (errorStr.contains('timeout')) {
        errorMessage = 'Request timeout. Please try again.';
      } else if (errorStr.contains('network')) {
        errorMessage = 'Network error. Please check your connection.';
      } else {
        errorMessage = 'Process failed: $e';
      }

      _showErrorSnackBar(errorMessage);
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });
      }
    }
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(0xFF38A169),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        margin: const EdgeInsets.all(16),
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(0xFFE53E3E),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        margin: const EdgeInsets.all(16),
        duration: const Duration(seconds: 4),
      ),
    );
  }

  void _resetForm() {
    setState(() {
      _selectedFileBytes = null;
      _selectedFile = null;
      _selectedFileName = null;
      _passwordController.clear();
      _passwordValidation = null;
    });
  }

  Color _getPasswordStrengthColor(String strength) {
    switch (strength.toLowerCase()) {
      case 'strong':
        return const Color(0xFF38A169);
      case 'medium':
        return const Color(0xFFED8936);
      default:
        return const Color(0xFFE53E3E);
    }
  }
}