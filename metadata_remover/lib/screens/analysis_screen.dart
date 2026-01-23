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
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Color(0xFF2D3748)),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Analysis Results',
          style: TextStyle(
            color: Color(0xFF2D3748),
            fontWeight: FontWeight.w600,
            fontSize: 18,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            color: const Color(0xFFE2E8F0),
            height: 1,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildFileInfoCard(),
            const SizedBox(height: 12),
            _buildRiskScoreCard(),
            const SizedBox(height: 12),
            _buildMetadataCountCard(),
            const SizedBox(height: 20),
            _buildMetadataSection(),
            const SizedBox(height: 20),
            _buildDownloadButton(),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildFileInfoCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFF7FAFC),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              _getFileIcon(widget.analysis.fileType),
              size: 32,
              color: const Color(0xFF4A5568),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.analysis.filename,
                  style: const TextStyle(
                    color: Color(0xFF2D3748),
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                Text(
                  widget.analysis.fileSizeFormatted,
                  style: const TextStyle(
                    color: Color(0xFF718096),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRiskScoreCard() {
    final riskColor = _getRiskColor(widget.analysis.riskScore);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Risk Assessment',
                style: TextStyle(
                  color: Color(0xFF2D3748),
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                decoration: BoxDecoration(
                  color: riskColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: riskColor.withOpacity(0.3), width: 1),
                ),
                child: Text(
                  widget.analysis.riskLevel,
                  style: TextStyle(
                    color: riskColor,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                height: 140,
                width: 140,
                child: CircularProgressIndicator(
                  value: widget.analysis.riskScore / 100,
                  strokeWidth: 10,
                  backgroundColor: const Color(0xFFF7FAFC),
                  valueColor: AlwaysStoppedAnimation<Color>(riskColor),
                ),
              ),
              Column(
                children: [
                  Text(
                    '${widget.analysis.riskScore}',
                    style: TextStyle(
                      color: riskColor,
                      fontSize: 42,
                      fontWeight: FontWeight.w700,
                      height: 1,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Risk Score',
                    style: TextStyle(
                      color: Color(0xFF718096),
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ],
          ),
          if (widget.analysis.riskRecommendation != null) ...[
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: riskColor.withOpacity(0.05),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: riskColor.withOpacity(0.2),
                  width: 1,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    color: riskColor,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      widget.analysis.riskRecommendation!,
                      style: const TextStyle(
                        color: Color(0xFF4A5568),
                        fontSize: 13,
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMetadataCountCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFEBF8FF),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.info_outline_rounded,
              color: Color(0xFF3182CE),
              size: 24,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Metadata Found',
                  style: TextStyle(
                    color: Color(0xFF718096),
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${widget.analysis.metadataCount} entries',
                  style: const TextStyle(
                    color: Color(0xFF2D3748),
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetadataSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Metadata Details',
          style: TextStyle(
            color: Color(0xFF2D3748),
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        ...widget.analysis.metadataEntries.map((entry) {
          final riskColor = _getRiskColorForLevel(entry.riskLevel);

          return Container(
            margin: const EdgeInsets.only(bottom: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE2E8F0), width: 1),
            ),
            child: Theme(
              data: Theme.of(context).copyWith(
                dividerColor: Colors.transparent,
              ),
              child: ExpansionTile(
                tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                childrenPadding: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: riskColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(
                    _getCategoryIcon(entry.category),
                    color: riskColor,
                    size: 20,
                  ),
                ),
                title: Text(
                  entry.key,
                  style: const TextStyle(
                    color: Color(0xFF2D3748),
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                  ),
                ),
                subtitle: Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    entry.category,
                    style: const TextStyle(
                      color: Color(0xFF718096),
                      fontSize: 12,
                    ),
                  ),
                ),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: riskColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: riskColor.withOpacity(0.3), width: 1),
                  ),
                  child: Text(
                    entry.riskLevel,
                    style: TextStyle(
                      color: riskColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                iconColor: const Color(0xFF4A5568),
                collapsedIconColor: const Color(0xFF718096),
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF7FAFC),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      entry.value,
                      style: const TextStyle(
                        color: Color(0xFF4A5568),
                        fontSize: 13,
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildDownloadButton() {
    return Container(
      decoration: BoxDecoration(
        color: _isDownloading ? const Color(0xFFE2E8F0) : const Color(0xFF3182CE),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _isDownloading ? null : _downloadCleanFile,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (_isDownloading)
                  const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.5,
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF4A5568)),
                    ),
                  )
                else
                  const Icon(Icons.download_rounded, color: Colors.white, size: 22),
                const SizedBox(width: 12),
                Text(
                  _isDownloading ? 'Downloading...' : 'Download Clean File',
                  style: TextStyle(
                    color: _isDownloading ? const Color(0xFF4A5568) : Colors.white,
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

  Future<void> _downloadCleanFile() async {
    setState(() {
      _isDownloading = true;
    });

    try {
      final Uint8List cleanedBytes =
      await _apiService.downloadCleanedFile(widget.analysis.id);

      if (!mounted) return;

      await downloadMobile(cleanedBytes, 'clean_${widget.analysis.filename}');

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('File downloaded successfully!'),
          backgroundColor: const Color(0xFF38A169),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Download failed: $e'),
          backgroundColor: const Color(0xFFE53E3E),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          margin: const EdgeInsets.all(16),
        ),
      );
    } finally {
      setState(() {
        _isDownloading = false;
      });
    }
  }

  IconData _getFileIcon(String fileType) {
    if (fileType.contains('image')) return Icons.image_rounded;
    if (fileType.contains('pdf')) return Icons.picture_as_pdf_rounded;
    if (fileType.contains('document')) return Icons.description_rounded;
    return Icons.insert_drive_file_rounded;
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'location':
        return Icons.location_on_rounded;
      case 'device':
        return Icons.phone_android_rounded;
      case 'software':
        return Icons.computer_rounded;
      case 'camera':
        return Icons.camera_alt_rounded;
      case 'personal':
        return Icons.person_rounded;
      case 'temporal':
        return Icons.access_time_rounded;
      default:
        return Icons.info_rounded;
    }
  }

  Color _getRiskColor(int riskScore) {
    if (riskScore >= 80) return const Color(0xFFE53E3E);
    if (riskScore >= 60) return const Color(0xFFED8936);
    if (riskScore >= 40) return const Color(0xFFECC94B);
    return const Color(0xFF38A169);
  }

  Color _getRiskColorForLevel(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return const Color(0xFFE53E3E);
      case 'high':
        return const Color(0xFFED8936);
      case 'medium':
        return const Color(0xFFECC94B);
      default:
        return const Color(0xFF38A169);
    }
  }
}