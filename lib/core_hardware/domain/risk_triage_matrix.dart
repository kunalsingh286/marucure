/// Determines the danger score based on the mining occupation.
double getPositionDangerScore(String occupationType) {
  switch (occupationType.toLowerCase()) {
    case 'stone_driller':
      return 2.5;
    case 'stone_cutter':
      return 2.0;
    case 'loading_transport':
      return 1.2;
    case 'administrative':
      return 0.2;
    default:
      return 1.0; 
  }
}

class TriageResult {
  final double score;
  final bool requiresCriticalDispatch;

  TriageResult({required this.score, required this.requiresCriticalDispatch});
}

/// Strict mathematical function calculating a normalized 1-10 Risk Index.
TriageResult calculateTriageRiskIndex({
  required double yearsExposure,
  required String occupationType,
  required double spirometryRatio,
  required double aiConfidenceScore,
}) {
  final double positionDanger = getPositionDangerScore(occupationType);
  
  // Vector 1: Exposure Risk (Cap years at 30 for normalization, max score 2.0)
  double normalizedExposure = (yearsExposure > 30 ? 30 : yearsExposure) / 30.0;
  double exposureVector = normalizedExposure * 2.0;

  // Vector 2: Position Danger (Max score 2.5)
  double positionVector = positionDanger;

  // Vector 3: Spirometry Risk (Inverted ratio. The lower the ratio, the higher the risk. Max score 2.5)
  // Healthy ratio > 0.8 is 0 risk. Clinical obstruction is < 0.7.
  double spirometryVector = 0.0;
  if (spirometryRatio < 0.8) {
    // Maps ratio from 0.8 -> 0.3 to a risk score of 0.0 -> 2.5
    double diff = 0.8 - spirometryRatio;
    if (diff > 0.5) diff = 0.5; // Cap at 0.3 ratio
    spirometryVector = (diff / 0.5) * 2.5;
  }

  // Vector 4: AI Confidence Risk (Directly proportional, max score 3.0)
  double aiVector = aiConfidenceScore * 3.0;

  // Total Matrix Score (Max 10.0)
  double totalScore = exposureVector + positionVector + spirometryVector + aiVector;
  if (totalScore > 10.0) totalScore = 10.0;
  if (totalScore < 1.0) totalScore = 1.0;

  // Any final score >= 7.5 triggers an absolute critical administrative dispatch recommendation flag.
  bool critical = totalScore >= 7.5;

  return TriageResult(
    score: double.parse(totalScore.toStringAsFixed(2)), 
    requiresCriticalDispatch: critical
  );
}
