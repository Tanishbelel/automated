import 'metadata_entry.dart';
class FileAnalysis {
  final String id;
  final String filename;
  final String fileType;
  final int fileSize;
  final String platform;
  final int riskScore;
  final int metadataCount;
  final String shareToken;
  final String status;
  final List<MetadataEntry> metadataEntries;
  final String? riskRecommendation;

  FileAnalysis({
    required this.id,
    required this.filename,
    required this.fileType,
    required this.fileSize,
    required this.platform,
    required this.riskScore,
    required this.metadataCount,
    required this.shareToken,
    required this.status,
    required this.metadataEntries,
    this.riskRecommendation,
  });

  factory FileAnalysis.fromJson(Map<String, dynamic> json) {
    return FileAnalysis(
      id: json['analysis_id'] ?? json['id'] ?? '',
      filename: json['filename'] ?? json['original_filename'] ?? '',
      fileType: json['file_type'] ?? '',
      fileSize: json['file_size'] ?? 0,
      platform: json['platform'] ?? 'general',
      riskScore: json['risk_score'] ?? 0,
      metadataCount: json['metadata_count'] ?? 0,
      shareToken: json['share_token'] ?? '',
      status: json['status'] ?? 'pending',
      metadataEntries: (json['metadata_entries'] as List<dynamic>?)
          ?.map((e) => MetadataEntry.fromJson(e))
          .toList() ??
          [],
      riskRecommendation: json['risk_recommendation'],
    );
  }

  String get riskLevel {
    if (riskScore >= 80) return 'Critical';
    if (riskScore >= 60) return 'High';
    if (riskScore >= 40) return 'Medium';
    return 'Low';
  }

  String get fileSizeFormatted {
    if (fileSize < 1024) return '$fileSize B';
    if (fileSize < 1024 * 1024) return '${(fileSize / 1024).toStringAsFixed(1)} KB';
    if (fileSize < 1024 * 1024 * 1024) {
      return '${(fileSize / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(fileSize / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }
}
