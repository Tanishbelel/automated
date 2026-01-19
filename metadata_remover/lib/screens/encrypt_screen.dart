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
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Mode selector
          SegmentedButton<bool>(
            segments: const [
              ButtonSegment(
                value: true,
                label: Text('Encrypt'),
                icon: Icon(Icons.lock),
              ),
              ButtonSegment(
                value: false,
                label: Text('Decrypt'),
                icon: Icon(Icons.lock_open),
              ),
            ],
            selected: {_isEncryptMode},
            onSelectionChanged: (Set<bool> newSelection) {
              setState(() {
                _isEncryptMode = newSelection.first;
                _selectedFileBytes = null;
                _selectedFileName = null;
                _passwordController.clear();
                _passwordValidation = null;
              });
            },
          ),
          const SizedBox(height: 24),

          // Info card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        _isEncryptMode ? Icons.shield : Icons.vpn_key,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _isEncryptMode
                              ? 'Password Protect Your Files'
                              : 'Unlock Protected Files',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _isEncryptMode
                        ? 'Add an extra layer of security by encrypting your files with a password.'
                        : 'Enter the password to decrypt and access your protected files.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // File selection
          if (_selectedFileName == null)
            OutlinedButton.icon(
              onPressed: _pickFile,
              icon: const Icon(Icons.file_upload),
              label: const Text('Select File'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            )
          else
            Card(
              child: ListTile(
                leading: const Icon(Icons.insert_drive_file),
                title: Text(_selectedFileName!),
                trailing: IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () {
                    setState(() {
                      _selectedFileBytes = null;
                      _selectedFileName = null;
                    });
                  },
                ),
              ),
            ),
          const SizedBox(height: 16),

          // Encryption method (only for encrypt mode)
          if (_isEncryptMode) ...[
            Text(
              'Encryption Method',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(
                  value: 'encrypt',
                  label: Text('Standard'),
                ),
                ButtonSegment(
                  value: 'zip',
                  label: Text('ZIP'),
                ),
                ButtonSegment(
                  value: 'pdf',
                  label: Text('PDF'),
                ),
              ],
              selected: {_encryptionMethod},
              onSelectionChanged: (Set<String> newSelection) {
                setState(() {
                  _encryptionMethod = newSelection.first;
                });
              },
            ),
            const SizedBox(height: 16),
          ],

          // Password input
          TextField(
            controller: _passwordController,
            obscureText: _obscurePassword,
            decoration: InputDecoration(
              labelText: 'Password',
              border: const OutlineInputBorder(),
              prefixIcon: const Icon(Icons.lock),
              suffixIcon: IconButton(
                icon: Icon(
                  _obscurePassword ? Icons.visibility : Icons.visibility_off,
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
          const SizedBox(height: 8),

          // Password strength indicator (only for encrypt mode)
          if (_isEncryptMode && _passwordValidation != null) ...[
            LinearProgressIndicator(
              value: _passwordValidation!.score / 100,
              backgroundColor: Colors.grey.shade200,
              color: _getPasswordStrengthColor(_passwordValidation!.strength),
              minHeight: 8,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Strength: ${_passwordValidation!.strength}',
                  style: TextStyle(
                    color: _getPasswordStrengthColor(_passwordValidation!.strength),
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text('${_passwordValidation!.score}/100'),
              ],
            ),
            if (_passwordValidation!.feedback.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...(_passwordValidation!.feedback.map((feedback) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, size: 16),
                    const SizedBox(width: 8),
                    Expanded(child: Text(feedback, style: const TextStyle(fontSize: 12))),
                  ],
                ),
              ))),
            ],
            const SizedBox(height: 16),
          ],

          // Process button
          ElevatedButton.icon(
            onPressed: (_selectedFileBytes != null &&
                _passwordController.text.isNotEmpty &&
                !_isProcessing)
                ? _processFile
                : null,
            icon: _isProcessing
                ? const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
                : Icon(_isEncryptMode ? Icons.lock : Icons.lock_open),
            label: Text(
              _isProcessing
                  ? 'Processing...'
                  : _isEncryptMode
                  ? 'Encrypt File'
                  : 'Decrypt File',
            ),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.all(16),
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
            ),
          ),
        ],
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
          const SnackBar(
            content: Text('File encrypted and downloaded successfully!'),
            backgroundColor: Colors.green,
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
          const SnackBar(
            content: Text('File decrypted and downloaded successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      }

      // Reset form
      setState(() {
        _selectedFileBytes = null;
        _selectedFileName = null;
        _passwordController.clear();
        _passwordValidation = null;
      });
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Process failed: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } finally {
      setState(() {
        _isProcessing = false;
      });
    }
  }


  Color _getPasswordStrengthColor(String strength) {
    switch (strength.toLowerCase()) {
      case 'strong':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      default:
        return Colors.red;
    }
  }
}