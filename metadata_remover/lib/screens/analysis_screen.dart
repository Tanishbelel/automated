import 'dart:typed_data';
import 'dart:io';
import 'package:flutter/material.dart';
import '../models/file_analysis.dart';
import '../services/api_service.dart';
import '../utils/mobile_download.dart';

class AnalysisScreen extends StatefulWidget {
  final FileAnalysis analysis;

  const AnalysisScreen({super.key, required this.analysis});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final ApiService _apiService = ApiService();
  bool _isDownloading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Results'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // File info card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      _getFileIcon(widget.analysis.fileType),
                      size: 48,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.analysis.filename,
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            widget.analysis.fileSizeFormatted,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Risk score card
            Card(
              color: _getRiskColor(widget.analysis.riskScore).withOpacity(0.1),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Risk Level',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: _getRiskColor(widget.analysis.riskScore),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            widget.analysis.riskLevel,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    LinearProgressIndicator(
                      value: widget.analysis.riskScore / 100,
                      backgroundColor: Colors.grey.shade200,
                      color: _getRiskColor(widget.analysis.riskScore),
                      minHeight: 8,
                    ),
                    const SizedBox(height: 8),
                    Text('${widget.analysis.riskScore}/100',
                        style: Theme.of(context).textTheme.titleLarge),
                    if (widget.analysis.riskRecommendation != null) ...[
                      const SizedBox(height: 8),
                      Text(widget.analysis.riskRecommendation!,
                          style: Theme.of(context).textTheme.bodyMedium,
                          textAlign: TextAlign.center),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Metadata count
            Card(
              child: ListTile(
                leading: const Icon(Icons.info_outline),
                title: const Text('Metadata Found'),
                trailing: Text(
                  '${widget.analysis.metadataCount}',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Metadata entries
            Text('Metadata Details', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            ...widget.analysis.metadataEntries.map((entry) {
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ExpansionTile(
                  leading: Icon(
                    _getCategoryIcon(entry.category),
                    color: _getRiskColorForLevel(entry.riskLevel),
                  ),
                  title: Text(entry.key),
                  subtitle: Text(entry.category),
                  trailing: Chip(
                    label: Text(entry.riskLevel, style: const TextStyle(fontSize: 10)),
                    backgroundColor: _getRiskColorForLevel(entry.riskLevel).withOpacity(0.2),
                  ),
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(16),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(entry.value, style: Theme.of(context).textTheme.bodyMedium),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 24),

            // Download button (mobile only)
            ElevatedButton.icon(
              onPressed: _isDownloading ? null : _downloadCleanFile,
              icon: _isDownloading
                  ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
                  : const Icon(Icons.download),
              label: Text(_isDownloading ? 'Downloading...' : 'Download Clean File'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _downloadCleanFile() async {
    setState(() {
      _isDownloading = true;
    });

    try {
      final Uint8List cleanedBytes =
      await _apiService.downloadCleanedFile(widget.analysis.id);

      if (!mounted) return;

      // Mobile-only download
      await downloadMobile(cleanedBytes, 'clean_${widget.analysis.filename}');

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('File downloaded successfully!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } finally {
      setState(() {
        _isDownloading = false;
      });
    }
  }

  IconData _getFileIcon(String fileType) {
    if (fileType.contains('image')) return Icons.image;
    if (fileType.contains('pdf')) return Icons.picture_as_pdf;
    if (fileType.contains('document')) return Icons.description;
    return Icons.insert_drive_file;
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'location':
        return Icons.location_on;
      case 'device':
        return Icons.phone_android;
      case 'software':
        return Icons.computer;
      case 'camera':
        return Icons.camera_alt;
      case 'personal':
        return Icons.person;
      case 'temporal':
        return Icons.access_time;
      default:
        return Icons.info;
    }
  }

  Color _getRiskColor(int riskScore) {
    if (riskScore >= 80) return Colors.red;
    if (riskScore >= 60) return Colors.orange;
    if (riskScore >= 40) return Colors.yellow.shade700;
    return Colors.green;
  }

  Color _getRiskColorForLevel(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.orange;
      case 'medium':
        return Colors.yellow.shade700;
      default:
        return Colors.green;
    }
  }
}
