import 'dart:async';
import 'dart:typed_data';
import 'dart:js_interop';

@JS('window.maruCureAI.loadModel')
external JSPromise _loadModel(JSString url);

@JS('window.maruCureAI.runInference')
external JSNumber _runInference(JSAny float32Array);

class MaruCureInferenceEngine {
  bool _isModelLoaded = false;

  Future<void> initializeEngine() async {
    if (_isModelLoaded) return;
    try {
      // Passes the WASM compilation barrier into the official tfjs runtime
      await _loadModel('assets/models/silicosis_detector.tflite'.toJS).toDart;
      _isModelLoaded = true;
      print("[INFO] JS-Interop TFJS-TFLite WASM Inference Core initialized successfully.");
    } catch (e) {
      print("[FATAL] Failed to load quantized edge asset via JS interop: $e");
    }
  }

  Future<double> runOnDeviceInference(Uint8List rawPixelBuffer) async {
    if (!_isModelLoaded) {
      await initializeEngine();
    }

    var inputTensor = rawPixelBuffer.buffer.asFloat32List();
    
    print("[EXEC] Invoking INT8 WebAssembly math operations loop via JS Interop...");
    double output = _runInference(inputTensor.toJS).toDartDouble;
    
    return output;
  }
}
