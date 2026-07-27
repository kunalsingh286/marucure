import 'dart:async';
import 'dart:typed_data';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

enum HazardState {
  normal,
  obstructive,
  invalid
}

class BiometricPayload {
  final double fev1;
  final double fvc;
  final double ratio;
  final HazardState hazardState;

  BiometricPayload({
    required this.fev1,
    required this.fvc,
    required this.ratio,
    required this.hazardState,
  });
}

class BleSpirometerService {
  // Medical SPIROMETER service & characteristic (Example standard/custom UUIDs)
  static const String SPIROMETER_SERVICE_UUID = '00001822-0000-1000-8000-00805f9b34fb'; // Pulse Oximetry / Respiratory
  static const String MEASUREMENT_CHAR_UUID = '00002a5e-0000-1000-8000-00805f9b34fb';

  BluetoothDevice? _connectedDevice;
  StreamSubscription<List<int>>? _notifySubscription;
  
  final StreamController<BiometricPayload> _biometricStreamController = StreamController<BiometricPayload>.broadcast();
  Stream<BiometricPayload> get biometricStream => _biometricStreamController.stream;

  /// Scans for nearby BLE Spirometers and establishes a secure MTU-optimized link.
  Future<void> connectToSpirometer() async {
    // Ensure BLE is available and turned on
    if (await FlutterBluePlus.adapterState.first != BluetoothAdapterState.on) {
      throw Exception("Bluetooth is not turned on.");
    }

    // Start scanning
    await FlutterBluePlus.startScan(
      withServices: [Guid(SPIROMETER_SERVICE_UUID)],
      timeout: const Duration(seconds: 15)
    );

    FlutterBluePlus.onScanResults.listen((results) async {
      if (results.isNotEmpty) {
        ScanResult r = results.last; 
        _connectedDevice = r.device;
        await FlutterBluePlus.stopScan();
        
        // Connect and optimize MTU
        await _connectedDevice!.connect(autoConnect: false);
        await _connectedDevice!.requestMtu(512); 
        
        await _discoverAndListen();
      }
    });
  }

  Future<void> _discoverAndListen() async {
    if (_connectedDevice == null) return;

    List<BluetoothService> services = await _connectedDevice!.discoverServices();
    
    for (BluetoothService service in services) {
      if (service.uuid.toString() == SPIROMETER_SERVICE_UUID) {
        for (BluetoothCharacteristic characteristic in service.characteristics) {
          if (characteristic.uuid.toString() == MEASUREMENT_CHAR_UUID) {
            
            // Enable notifications
            await characteristic.setNotifyValue(true);
            
            // Intercept incoming byte arrays
            _notifySubscription = characteristic.onValueReceived.listen((value) {
              final payload = _decodeSpirometryPacket(value);
              if (payload != null) {
                _biometricStreamController.add(payload);
              }
            });
          }
        }
      }
    }
  }

  /// Raw byte-array packet parser.
  /// Expects an 8-byte array:
  /// Bytes 0-3: FEV1 (32-bit Float, Little Endian)
  /// Bytes 4-7: FVC (32-bit Float, Little Endian)
  BiometricPayload? _decodeSpirometryPacket(List<int> packet) {
    if (packet.length < 8) return null;

    final byteData = ByteData.sublistView(Uint8List.fromList(packet));
    
    // Isolate float bytes
    final double fev1 = byteData.getFloat32(0, Endian.little);
    final double fvc = byteData.getFloat32(4, Endian.little);

    if (fvc <= 0) return BiometricPayload(fev1: fev1, fvc: fvc, ratio: 0, hazardState: HazardState.invalid);

    // Compute FEV1/FVC ratio
    final double ratio = fev1 / fvc;

    // Evaluate hazard state (clinical threshold of 0.70)
    HazardState state = (ratio < 0.70) ? HazardState.obstructive : HazardState.normal;

    return BiometricPayload(
      fev1: fev1,
      fvc: fvc,
      ratio: ratio,
      hazardState: state,
    );
  }

  // Exposed for unit testing without BLE connection
  BiometricPayload? testDecodePacket(List<int> packet) {
    return _decodeSpirometryPacket(packet);
  }

  Future<void> disconnect() async {
    await _notifySubscription?.cancel();
    await _connectedDevice?.disconnect();
    _connectedDevice = null;
  }
}
