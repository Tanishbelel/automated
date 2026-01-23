import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import '../models/file_analysis.dart';
import 'analysis_screen.dart';
import 'encrypt_screen.dart';
import '../utils/mobile_download.dart';
import 'home_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  String? _error;
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildAppBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          bottom: BorderSide(color: const Color(0xFFE2E8F0), width: 1),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _selectedIndex == 0
                    ? 'Hey, User'
                    : _selectedIndex == 1
                    ? 'Encrypt Files'
                    : 'History',
                style: const TextStyle(
                  color: Color(0xFF2D3748),
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _selectedIndex == 0
                    ? 'Protect your privacy today'
                    : _selectedIndex == 1
                    ? 'Secure your files'
                    : 'Your analysis records',
                style: const TextStyle(
                  color: Color(0xFF718096),
                  fontSize: 14,
                ),
              ),
            ],
          ),
          Row(
            children: [
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF7FAFC),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
                ),
                child: IconButton(
                  icon: const Icon(Icons.person_rounded,
                      color: Color(0xFF4A5568)),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => const ProfileScreen(),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(width: 8),
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF7FAFC),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
                ),
                child: IconButton(
                  icon: const Icon(Icons.info_outline,
                      color: Color(0xFF4A5568)),
                  onPressed: _showAboutDialog,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBottomNav() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
        border: Border(
          top: BorderSide(color: const Color(0xFFE2E8F0), width: 1),
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(Icons.home_rounded, 'Home', 0),
              _buildNavItem(Icons.lock_rounded, 'Encrypt', 1),
              _buildNavItem(Icons.history_rounded, 'History', 2),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(IconData icon, String label, int index) {
    final isSelected = _selectedIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _selectedIndex = index),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF3182CE) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: isSelected ? Colors.white : const Color(0xFF718096),
              size: 22,
            ),
            if (isSelected) ...[
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_selectedIndex == 1) return const EncryptScreen();
    if (_selectedIndex == 2) return _buildHistoryView();
    return _buildHomeView();
  }

  Widget _buildHomeView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildHeroCard(),
          const SizedBox(height: 16),
          _buildActionButtons(),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(
                child: CircularProgressIndicator(
                  valueColor:
                  AlwaysStoppedAnimation<Color>(Color(0xFF3182CE)),
                ),
              ),
            ),
          if (_error != null) _buildErrorCard(),
          const SizedBox(height: 24),
          const Text(
            'Features',
            style: TextStyle(
              color: Color(0xFF2D3748),
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          _buildFeatureCard(
            icon: Icons.security_rounded,
            title: 'Privacy First',
            description:
            'All processing happens securely with no data stored permanently',
            color: const Color(0xFF3182CE),
          ),
          const SizedBox(height: 10),
          _buildFeatureCard(
            icon: Icons.speed_rounded,
            title: 'Fast Processing',
            description: 'Get your cleaned files in seconds',
            color: const Color(0xFFE53E3E),
          ),
          const SizedBox(height: 10),
          _buildFeatureCard(
            icon: Icons.check_circle_rounded,
            title: 'Multiple Formats',
            description: 'Support for images, PDFs, documents, and more',
            color: const Color(0xFF38A169),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroCard() {
    return Container(
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: const Color(0xFF3182CE),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.shield_rounded,
                size: 56, color: Colors.white),
          ),
          const SizedBox(height: 20),
          const Text(
            'Protect Your Privacy',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Remove hidden metadata from your files before sharing',
            style: TextStyle(
              color: Colors.white.withOpacity(0.9),
              fontSize: 14,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Column(
      children: [
        _buildPrimaryButton(
          icon: Icons.analytics_rounded,
          label: 'Analyze File',
          onPressed: _isLoading ? null : _analyzeFile,
        ),
        const SizedBox(height: 10),
        _buildSecondaryButton(
          icon: Icons.cleaning_services_rounded,
          label: 'Quick Clean & Download',
          onPressed: _isLoading ? null : _quickClean,
        ),
      ],
    );
  }

  Widget _buildPrimaryButton({
    required IconData icon,
    required String label,
    required VoidCallback? onPressed,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: onPressed != null
            ? const Color(0xFF3182CE)
            : const Color(0xFFE2E8F0),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  color:
                  onPressed != null ? Colors.white : const Color(0xFF718096),
                  size: 22,
                ),
                const SizedBox(width: 12),
                Text(
                  label,
                  style: TextStyle(
                    color: onPressed != null
                        ? Colors.white
                        : const Color(0xFF718096),
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

  Widget _buildSecondaryButton({
    required IconData icon,
    required String label,
    required VoidCallback? onPressed,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color(0xFF3182CE),
          width: 2,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, color: const Color(0xFF3182CE), size: 22),
                const SizedBox(width: 12),
                Text(
                  label,
                  style: const TextStyle(
                    color: Color(0xFF3182CE),
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

  Widget _buildErrorCard() {
    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF5F5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE53E3E).withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFE53E3E)),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _error!,
              style: const TextStyle(color: Color(0xFFE53E3E)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required IconData icon,
    required String title,
    required String description,
    required Color color,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: Color(0xFF2D3748),
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
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
      ),
    );
  }

  Widget _buildHistoryView() {
    return FutureBuilder<List<FileAnalysis>>(
      future: _apiService.getAnalysisHistory(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF3182CE)),
            ),
          );
        }
        if (snapshot.hasError) {
          return Center(
            child: Text(
              'Error loading history: ${snapshot.error}',
              style: const TextStyle(color: Color(0xFF718096)),
            ),
          );
        }
        final analyses = snapshot.data ?? [];
        if (analyses.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.history_rounded,
                    size: 80, color: const Color(0xFFCBD5E0)),
                const SizedBox(height: 16),
                const Text(
                  'No analysis history yet',
                  style: TextStyle(color: Color(0xFF718096), fontSize: 16),
                ),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: analyses.length,
          itemBuilder: (context, index) {
            final analysis = analyses[index];
            return Container(
              margin: const EdgeInsets.only(bottom: 10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            AnalysisScreen(analysis: analysis),
                      ),
                    );
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: _getRiskColor(analysis.riskScore)
                                .withOpacity(0.1),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            _getFileIcon(analysis.fileType),
                            color: _getRiskColor(analysis.riskScore),
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                analysis.filename,
                                style: const TextStyle(
                                  color: Color(0xFF2D3748),
                                  fontWeight: FontWeight.w600,
                                  fontSize: 15,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '${analysis.fileSizeFormatted} • Risk: ${analysis.riskLevel}',
                                style: const TextStyle(
                                  color: Color(0xFF718096),
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const Icon(
                          Icons.chevron_right_rounded,
                          color: Color(0xFF718096),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  Future<void> _analyzeFile() async {
    final result = await FilePicker.platform.pickFiles();
    if (result == null) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final pickedFile = result.files.single;
      dynamic fileData =
      pickedFile.path != null ? File(pickedFile.path!) : pickedFile.bytes!;
      final analysis =
      await _apiService.analyzeFile(fileData, pickedFile.name);

      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
            builder: (context) => AnalysisScreen(analysis: analysis)),
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _quickClean() async {
    final result = await FilePicker.platform.pickFiles();
    if (result == null) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final pickedFile = result.files.single;
      dynamic fileData =
      pickedFile.path != null ? File(pickedFile.path!) : pickedFile.bytes!;
      final cleanedBytes =
      await _apiService.cleanAndDownload(fileData, pickedFile.name);

      if (!mounted) return;

      await downloadMobile(cleanedBytes, 'clean_${pickedFile.name}');

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('File cleaned and downloaded successfully!'),
          backgroundColor: const Color(0xFF38A169),
          behavior: SnackBarBehavior.floating,
          shape:
          RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showAboutDialog() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Color(0xFF3182CE),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.shield_rounded,
                    size: 48, color: Colors.white),
              ),
              const SizedBox(height: 16),
              const Text(
                'Metadata Remover',
                style: TextStyle(
                  color: Color(0xFF2D3748),
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Version 1.0.0',
                style: TextStyle(
                  color: Color(0xFF718096),
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'Protect your privacy by removing hidden metadata from your files.',
                style: TextStyle(
                  color: Color(0xFF4A5568),
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  style: TextButton.styleFrom(
                    backgroundColor: const Color(0xFF3182CE),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text(
                    'Close',
                    style: TextStyle(
                        color: Colors.white, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  IconData _getFileIcon(String fileType) {
    if (fileType.contains('image')) return Icons.image_rounded;
    if (fileType.contains('pdf')) return Icons.picture_as_pdf_rounded;
    if (fileType.contains('document')) return Icons.description_rounded;
    return Icons.insert_drive_file_rounded;
  }

  Color _getRiskColor(int riskScore) {
    if (riskScore >= 80) return const Color(0xFFE53E3E);
    if (riskScore >= 60) return const Color(0xFFED8936);
    if (riskScore >= 40) return const Color(0xFFECC94B);
    return const Color(0xFF38A169);
  }
}