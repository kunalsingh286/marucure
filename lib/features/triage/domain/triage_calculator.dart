class TriageCalculator {
  /// Calculates the Unified Score (1-10) based on the exact clinical diagnostic formula
  /// mandated by the MaruCure architecture:
  /// (Years of Exposure * 0.3) + (Job Hazard Weight * 0.2) + (Spirometry Obstruction * 0.2) + (AI Core Score * 0.3)
  static double computeUnifiedScore({
    required double yearsOfExposure,
    required double jobHazardWeight, // 1.0 to 10.0 scale based on dust intensity (e.g. Stone Driller = high)
    required double spirometryRatio, // FEV1/FVC ratio
    required double aiConfidenceScore, // 1.0 to 10.0 scale from WASM model
  }) {
    // 1. Normalize Years of Exposure (Assume 30 years is max for a 10.0 score)
    double normalizedExposure = (yearsOfExposure / 30.0) * 10.0;
    if (normalizedExposure > 10.0) normalizedExposure = 10.0;

    // 2. Normalize Spirometry Obstruction (Lower ratio = Higher risk)
    // Clinical flag threshold is 0.70. If ratio is 0.50, obstruction risk is very high (10.0).
    // If ratio is 0.85, obstruction risk is very low (1.0).
    double obstructionScore = 0.0;
    if (spirometryRatio <= 0.50) {
      obstructionScore = 10.0;
    } else if (spirometryRatio >= 0.85) {
      obstructionScore = 1.0;
    } else {
      // Linear scaling between 0.85 and 0.50 mapping to 1.0 - 10.0
      obstructionScore = 1.0 + ((0.85 - spirometryRatio) / (0.85 - 0.50)) * 9.0;
    }

    // 3. Compute final weighted formula
    double finalScore = (normalizedExposure * 0.3) +
                        (jobHazardWeight * 0.2) +
                        (obstructionScore * 0.2) +
                        (aiConfidenceScore * 0.3);

    // Bound between 1 and 10
    if (finalScore < 1.0) return 1.0;
    if (finalScore > 10.0) return 10.0;

    return finalScore;
  }
}
