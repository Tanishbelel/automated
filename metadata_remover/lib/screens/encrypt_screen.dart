import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';
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
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildModeSelector(),
          const SizedBox(height: 24),
          _buildInfoCard(),
          const SizedBox(height: 24),
          _buildFileSelection(),
          const SizedBox(height: 20),
          if (_isEncryptMode) ...[
            _buildEncryptionMethodSelector(),
            const SizedBox(height: 20),
          ],
          _buildPasswordField(),
          const SizedBox(height: 12),
          if (_isEncryptMode && _passwordValidation != null) ...[
            _buildPasswordStrengthIndicator(),
            const SizedBox(height: 20),
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
        color: const Color(0xFF2A2336),
        borderRadius: BorderRadius.circular(16),
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
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          gradient: isSelected
              ? const LinearGradient(
            colors: [Color(0xFF7B61FF), Color(0xFF9D7EFF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          )
              : null,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: Colors.white,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
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
        gradient: LinearGradient(
          colors: _isEncryptMode
              ? [const Color(0xFF7B61FF).withOpacity(0.2), const Color(0xFF9D7EFF).withOpacity(0.1)]
              : [const Color(0xFF4ECDC4).withOpacity(0.2), const Color(0xFF44A39D).withOpacity(0.1)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: (_isEncryptMode ? const Color(0xFF7B61FF) : const Color(0xFF4ECDC4)).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: _isEncryptMode
                    ? [const Color(0xFF7B61FF), const Color(0xFF9D7EFF)]
                    : [const Color(0xFF4ECDC4), const Color(0xFF44A39D)],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              _isEncryptMode ? Icons.shield_rounded : Icons.vpn_key_rounded,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isEncryptMode ? 'Password Protect Your Files' : 'Unlock Protected Files',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _isEncryptMode
                      ? 'Add an extra layer of security with encryption.'
                      : 'Enter password to decrypt your files.',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
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
            color: const Color(0xFF2A2336),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: const Color(0xFF7B61FF).withOpacity(0.3),
              width: 1.5,
            ),
          ),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF7B61FF).withOpacity(0.2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.cloud_upload_rounded,
                  color: Color(0xFF7B61FF),
                  size: 40,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Select File',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Tap to choose a file',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
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
        color: const Color(0xFF2A2336),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: const Color(0xFF7B61FF).withOpacity(0.2),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.insert_drive_file_rounded,
              color: Color(0xFF7B61FF),
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _selectedFileName!,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w500,
                fontSize: 14,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded, color: Colors.white70),
            onPressed: () {
              setState(() {
                _selectedFileBytes = null;
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
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: const Color(0xFF2A2336),
            borderRadius: BorderRadius.circular(16),
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
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF7B61FF) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: Colors.white,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
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
        color: const Color(0xFF2A2336),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF7B61FF).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: TextField(
        controller: _passwordController,
        obscureText: _obscurePassword,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          labelText: 'Password',
          labelStyle: TextStyle(color: Colors.white.withOpacity(0.6)),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.all(16),
          prefixIcon: const Icon(Icons.lock_rounded, color: Color(0xFF7B61FF)),
          suffixIcon: IconButton(
            icon: Icon(
              _obscurePassword ? Icons.visibility_rounded : Icons.visibility_off_rounded,
              color: Colors.white.withOpacity(0.6),
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
        color: const Color(0xFF2A2336),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Password Strength',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.8),
                  fontSize: 13,
                ),
              ),
              Text(
                '${_passwordValidation!.score}/100',
                style: TextStyle(
                  color: _getPasswordStrengthColor(_passwordValidation!.strength),
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: _passwordValidation!.score / 100,
              backgroundColor: Colors.white.withOpacity(0.1),
              color: _getPasswordStrengthColor(_passwordValidation!.strength),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: _getPasswordStrengthColor(_passwordValidation!.strength).withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              _passwordValidation!.strength.toUpperCase(),
              style: TextStyle(
                color: _getPasswordStrengthColor(_passwordValidation!.strength),
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
          if (_passwordValidation!.feedback.isNotEmpty) ...[
            const SizedBox(height: 12),
            ...(_passwordValidation!.feedback.map((feedback) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: 16,
                    color: Colors.white.withOpacity(0.6),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      feedback,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withOpacity(0.7),
                      ),
                    ),
                  ),
                ],
              ),
            ))),
          ],
        ],
      ),
    );
  }

  Widget _buildProcessButton() {
    final isEnabled = _selectedFileBytes != null &&
        _passwordController.text.isNotEmpty &&
        !_isProcessing;

    return Container(
      decoration: BoxDecoration(
        gradient: isEnabled
            ? const LinearGradient(
          colors: [Color(0xFF7B61FF), Color(0xFF9D7EFF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        )
            : null,
        color: !isEnabled ? const Color(0xFF2A2336) : null,
        borderRadius: BorderRadius.circular(16),
        boxShadow: isEnabled
            ? [
          BoxShadow(
            color: const Color(0xFF7B61FF).withOpacity(0.3),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isEnabled ? _processFile : null,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 18),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (_isProcessing)
                  const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                else
                  Icon(
                    _isEncryptMode ? Icons.lock_rounded : Icons.lock_open_rounded,
                    color: Colors.white,
                  ),
                const SizedBox(width: 12),
                Text(
                  _isProcessing
                      ? 'Processing...'
                      : _isEncryptMode
                      ? 'Encrypt File'
                      : 'Decrypt File',
                  style: const TextStyle(
                    color: Colors.white,
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
    final result = await FilePicker.platform.pickFiles();

    if (result != null) {
      setState(() {
        _selectedFileBytes = result.files.single.bytes;
        _selectedFileName = result.files.single.name;
      });
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
      setState(() {
        _passwordValidation = validation;
      });
    } catch (e) {
      // Handle error silently
    }
  }

  Future<void> _processFile() async {
    if (_selectedFileBytes == null || _passwordController.text.isEmpty) return;

    setState(() {
      _isProcessing = true;
    });

    try {
      Uint8List resultBytes;
      String downloadFileName;

      if (_isEncryptMode) {
        // Encrypt
        resultBytes = await _apiService.encryptFile(
          _selectedFileBytes!,
          _selectedFileName!,
          _passwordController.text,
          _encryptionMethod,
        );

        final extension = _encryptionMethod == 'zip'
            ? 'zip'
            : _encryptionMethod == 'pdf'
            ? 'pdf'
            : 'enc';
        downloadFileName = '${_selectedFileName}_protected.$extension';

        // Mobile download
        await downloadMobile(resultBytes, downloadFileName);

        if (!mounted) return;

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('File encrypted and downloaded successfully!'),
            backgroundColor: const Color(0xFF4ECDC4),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      } else {
        // Decrypt
        resultBytes = await _apiService.decryptFile(
          _selectedFileBytes!,
          _selectedFileName!,
          _passwordController.text,
        );

        downloadFileName = '${_selectedFileName}_decrypted';

        // Mobile download
        await downloadMobile(resultBytes, downloadFileName);

        if (!mounted) return;

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('File decrypted and downloaded successfully!'),
            backgroundColor: const Color(0xFF4ECDC4),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }

      // Reset form
      _resetForm();
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Process failed: $e'),
          backgroundColor: const Color(0xFFFF6B9D),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }

  void _resetForm() {
    _selectedFileBytes = null;
    _selectedFileName = null;
    _passwordController.clear();
    _passwordValidation = null;
  }

  Color _getPasswordStrengthColor(String strength) {
    switch (strength.toLowerCase()) {
      case 'strong':
        return const Color(0xFF4ECDC4);
      case 'medium':
        return const Color(0xFFFFB74D);
      default:
        return const Color(0xFFFF6B9D);
    }
  }
}