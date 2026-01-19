class PasswordValidation {
  final bool isValid;
  final int score;
  final List<String> feedback;
  final String strength;

  PasswordValidation({
    required this.isValid,
    required this.score,
    required this.feedback,
    required this.strength,
  });

  factory PasswordValidation.fromJson(Map<String, dynamic> json) {
    return PasswordValidation(
      isValid: json['is_valid'] ?? false,
      score: json['score'] ?? 0,
      feedback: List<String>.from(json['feedback'] ?? []),
      strength: json['strength'] ?? 'weak',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'is_valid': isValid,
      'score': score,
      'feedback': feedback,
      'strength': strength,
    };
  }
}