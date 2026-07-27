class ScreeningEntity {
  final String id;
  final String fullName;
  final String janAadhaarNumber;
  final double riskIndexScore;
  final String clinicalFlag;
  final String syncStatus;

  ScreeningEntity({
    required this.id,
    required this.fullName,
    required this.janAadhaarNumber,
    required this.riskIndexScore,
    required this.clinicalFlag,
    this.syncStatus = 'pending',
  });

  bool get isHighRisk => riskIndexScore >= 7.5 || clinicalFlag == 'FIR';

  factory ScreeningEntity.fromMap(Map<String, dynamic> map) {
    return ScreeningEntity(
      id: map['id'] as String,
      fullName: map['full_name'] as String,
      janAadhaarNumber: map['jan_aadhaar_number'] as String,
      riskIndexScore: (map['risk_index_score'] as num).toDouble(),
      clinicalFlag: map['clinical_flag'] as String,
      syncStatus: map['sync_status'] as String? ?? 'pending',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'full_name': fullName,
      'jan_aadhaar_number': janAadhaarNumber,
      'risk_index_score': riskIndexScore,
      'clinical_flag': clinicalFlag,
      'sync_status': syncStatus,
    };
  }
}
