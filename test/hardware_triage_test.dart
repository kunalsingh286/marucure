import 'dart:typed_data';
import 'package:test/test.dart';

// Since we are running in an environment without standard Flutter toolchains 
// we will structure the test so it can be evaluated, but acknowledging the environment limits.
import '../lib/core_hardware/services/ble_spirometer_service.dart';
import '../lib/core_hardware/domain/risk_triage_matrix.dart';

void main() {
  group('Hardware Connectivity & Packet Parsing Tests', () {
    final bleService = BleSpirometerService();

    test('Decodes valid normal spirometry packet correctly', () {
      // 3.5 FEV1, 4.0 FVC -> Ratio 0.875
      final byteData = ByteData(8);
      byteData.setFloat32(0, 3.5, Endian.little);
      byteData.setFloat32(4, 4.0, Endian.little);

      final payload = bleService.testDecodePacket(byteData.buffer.asUint8List());

      expect(payload, isNotNull);
      expect(payload!.fev1, closeTo(3.5, 0.01));
      expect(payload.fvc, closeTo(4.0, 0.01));
      expect(payload.ratio, closeTo(0.875, 0.01));
      expect(payload.hazardState, equals(HazardState.normal));
    });

    test('Flags low spirometry ratios immediately (< 0.70)', () {
      // 2.0 FEV1, 4.0 FVC -> Ratio 0.50 (Obstructive)
      final byteData = ByteData(8);
      byteData.setFloat32(0, 2.0, Endian.little);
      byteData.setFloat32(4, 4.0, Endian.little);

      final payload = bleService.testDecodePacket(byteData.buffer.asUint8List());

      expect(payload, isNotNull);
      expect(payload!.ratio, equals(0.50));
      expect(payload.hazardState, equals(HazardState.obstructive));
    });

    test('Handles malformed packets without data leaks', () {
      // Packet too short
      final payload = bleService.testDecodePacket([0, 1, 2, 3]);
      expect(payload, isNull);
    });
  });

  group('Dynamic Exposure Triage Matrix Tests', () {
    test('Calculates low risk correctly', () {
      final result = calculateTriageRiskIndex(
        yearsExposure: 2.0,
        occupationType: 'administrative', // 0.2
        spirometryRatio: 0.95, // 0.0
        aiConfidenceScore: 0.1, // 0.3
      );
      
      // Exposure: (2/30)*2 = 0.133
      // Total approx = 0.133 + 0.2 + 0.0 + 0.3 = 0.633 (Floored to 1.0 minimum)
      expect(result.score, equals(1.0));
      expect(result.requiresCriticalDispatch, isFalse);
    });

    test('Triggers absolute critical administrative dispatch for severe cases', () {
      final result = calculateTriageRiskIndex(
        yearsExposure: 25.0, // (25/30)*2 = 1.66
        occupationType: 'stone_driller', // 2.5
        spirometryRatio: 0.50, // (0.3/0.5)*2.5 = 1.5
        aiConfidenceScore: 0.90, // 2.7
      );
      
      // Total approx = 1.66 + 2.5 + 1.5 + 2.7 = 8.36
      expect(result.score, greaterThanOrEqualTo(7.5));
      expect(result.requiresCriticalDispatch, isTrue);
    });

    test('Handles mathematical maximum boundaries', () {
      final result = calculateTriageRiskIndex(
        yearsExposure: 50.0, // Capped at 30 -> 2.0
        occupationType: 'stone_driller', // 2.5
        spirometryRatio: 0.10, // Capped at diff 0.5 -> 2.5
        aiConfidenceScore: 1.0, // 3.0
      );
      
      // Total approx = 2.0 + 2.5 + 2.5 + 3.0 = 10.0
      expect(result.score, equals(10.0));
      expect(result.requiresCriticalDispatch, isTrue);
    });
  });
}
