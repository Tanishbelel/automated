import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import '../models/file_analysis.dart';
import 'analysis_screen.dart';
import 'encrypt_screen.dart';
import '../utils/mobile_download.dart'; // mobile-only download

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
      appBar: AppBar(
        title: const Text('Metadata Remover'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showAboutDialog,
          ),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() => _selectedIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.lock_outlined),
            selectedIcon: Icon(Icons.lock),
            label: 'Encrypt',
          ),
          NavigationDestination(
            icon: Icon(Icons.history),
            selectedIcon: Icon(Icons.history),
            label: 'History',
          ),
        ],
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
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(Icons.shield_outlined, size: 80, color: Theme.of(context).colorScheme.primary),
                  const SizedBox(height: 16),
                  Text('Protect Your Privacy',
                      style: Theme.of(context).textTheme.headlineSmall,
                      textAlign: TextAlign.center),
                  const SizedBox(height: 8),
                  Text('Remove hidden metadata from your files before sharing',
                      style: Theme.of(context).textTheme.bodyMedium,
                      textAlign: TextAlign.center),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _isLoading ? null : _analyzeFile,
            icon: const Icon(Icons.analytics),
            label: const Text('Analyze File'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.all(16),
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: _isLoading ? null : _quickClean,
            icon: const Icon(Icons.cleaning_services),
            label: const Text('Quick Clean & Download'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.all(16),
            ),
          ),
          if (_isLoading) const Padding(
            padding: EdgeInsets.all(24),
            child: Center(child: CircularProgressIndicator()),
          ),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Card(
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(_error!,
                            style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer)),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          const SizedBox(height: 24),
          _buildFeatureCard(
            icon: Icons.security,
            title: 'Privacy First',
            description: 'All processing happens securely with no data stored permanently',
          ),
          const SizedBox(height: 12),
          _buildFeatureCard(
            icon: Icons.speed,
            title: 'Fast Processing',
            description: 'Get your cleaned files in seconds',
          ),
          const SizedBox(height: 12),
          _buildFeatureCard(
            icon: Icons.check_circle,
            title: 'Multiple Formats',
            description: 'Support for images, PDFs, documents, and more',
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({required IconData icon, required String title, required String description}) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(description),
      ),
    );
  }

  Widget _buildHistoryView() {
    return FutureBuilder<List<FileAnalysis>>(
      future: _apiService.getAnalysisHistory(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Text('Error loading history: ${snapshot.error}'));
        final analyses = snapshot.data ?? [];
        if (analyses.isEmpty) return const Center(child: Text('No analysis history yet'));

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: analyses.length,
          itemBuilder: (context, index) {
            final analysis = analyses[index];
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: ListTile(
                leading: Icon(_getFileIcon(analysis.fileType), color: _getRiskColor(analysis.riskScore)),
                title: Text(analysis.filename),
                subtitle: Text('${analysis.fileSizeFormatted} • Risk: ${analysis.riskLevel}'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  Navigator.push(context,
                      MaterialPageRoute(builder: (context) => AnalysisScreen(analysis: analysis)));
                },
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

    setState(() { _isLoading = true; _error = null; });

    try {
      final pickedFile = result.files.single;
      dynamic fileData = pickedFile.path != null ? File(pickedFile.path!) : pickedFile.bytes!;
      final analysis = await _apiService.analyzeFile(fileData, pickedFile.name);

      if (!mounted) return;
      Navigator.push(context, MaterialPageRoute(builder: (context) => AnalysisScreen(analysis: analysis)));
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  Future<void> _quickClean() async {
    final result = await FilePicker.platform.pickFiles();
    if (result == null) return;

    setState(() { _isLoading = true; _error = null; });

    try {
      final pickedFile = result.files.single;
      dynamic fileData = pickedFile.path != null ? File(pickedFile.path!) : pickedFile.bytes!;
      final cleanedBytes = await _apiService.cleanAndDownload(fileData, pickedFile.name);

      if (!mounted) return;

      // Save file on mobile
      await downloadMobile(cleanedBytes, 'clean_${pickedFile.name}');

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('File cleaned and downloaded successfully!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      setState(() { _error = e.toString(); });
    } finally {
      setState(() { _isLoading = false; });
    }
  }

  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: 'Metadata Remover',
      applicationVersion: '1.0.0',
      applicationIcon: const Icon(Icons.shield, size: 48),
      children: const [
        Text('Protect your privacy by removing hidden metadata from your files.'),
      ],
    );
  }

  IconData _getFileIcon(String fileType) {
    if (fileType.contains('image')) return Icons.image;
    if (fileType.contains('pdf')) return Icons.picture_as_pdf;
    if (fileType.contains('document')) return Icons.description;
    return Icons.insert_drive_file;
  }

  Color _getRiskColor(int riskScore) {
    if (riskScore >= 80) return Colors.red;
    if (riskScore >= 60) return Colors.orange;
    if (riskScore >= 40) return Colors.yellow.shade700;
    return Colors.green;
  }
}
