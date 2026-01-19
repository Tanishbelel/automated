class MetadataEntry {
  final String key;
  final String value;
  final String category;
  final String riskLevel;

  MetadataEntry({
    required this.key,
    required this.value,
    required this.category,
    required this.riskLevel,
  });

  factory MetadataEntry.fromJson(Map<String, dynamic> json) {
    return MetadataEntry(
      key: json['key'] ?? '',
      value: json['value'] ?? '',
      category: json['category'] ?? '',
      riskLevel: json['risk_level'] ?? 'low',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'key': key,
      'value': value,
      'category': category,
      'risk_level': riskLevel,
    };
  }
}