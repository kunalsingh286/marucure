import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image/image.dart' as img;

import '../core/crypto/wasm_inference.dart';
import '../features/triage/presentation/state/triage_state_manager.dart';
import '../features/triage/data/bluetooth_spirometer_service.dart';

class WebDashboard extends StatefulWidget {
  @override
  _WebDashboardState createState() => _WebDashboardState();
}

class _WebDashboardState extends State<WebDashboard> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MARUCURE // OFFLINE PWA NODE'),
        actions: [
          Row(
            children: [
              const Text('Hardware Emulator'),
              Switch(
                value: WebSpirometerConnector.isEmulatorEnabled,
                onChanged: (val) {
                  setState(() {
                    WebSpirometerConnector.isEmulatorEnabled = val;
                  });
                },
              ),
              const SizedBox(width: 20),
            ],
          )
        ],
      ),
      body: Row(
        children: [
          // Left Pane: Navigation / Queue
          Expanded(
            flex: 2,
            child: Consumer<TriageStateManager>(
              builder: (context, state, child) {
                return Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: ElevatedButton.icon(
                        onPressed: state.isSyncing ? null : state.syncOutbox,
                        icon: state.isSyncing ? const CircularProgressIndicator(color: Colors.white) : const Icon(Icons.sync),
                        label: Text(state.isSyncing ? 'Syncing...' : 'Sync to SDC (Outbox)'),
                        style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50)),
                      ),
                    ),
                    Expanded(
                      child: ListView.builder(
                        itemCount: state.queue.length,
                        itemBuilder: (context, index) {
                          final item = state.queue[index];
                          final isPending = item.syncStatus == 'pending';
                          return ListTile(
                            leading: Icon(
                              isPending ? Icons.hourglass_empty : Icons.check_circle,
                              color: isPending ? Colors.orange : Colors.green,
                            ),
                            title: Text(item.fullName),
                            subtitle: Text('ID: ${item.janAadhaarNumber}'),
                            trailing: Text('Risk: ${item.riskIndexScore}'),
                          );
                        },
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
          const VerticalDivider(width: 1),
          // Right Pane: Diagnostic View & WASM Inference
          Expanded(
            flex: 5,
            child: DiagnosticViewPane(),
          ),
        ],
      ),
    );
  }
}

class DiagnosticViewPane extends StatefulWidget {
  @override
  _DiagnosticViewPaneState createState() => _DiagnosticViewPaneState();
}

class _DiagnosticViewPaneState extends State<DiagnosticViewPane> {
  String _inferenceStatus = "Waiting for X-Ray input...";
  Uint8List? _displayImageBytes;
  final ImagePicker _picker = ImagePicker();
  final _inferenceEngine = MaruCureInferenceEngine();

  Future<void> _pickAndAnalyzeImage() async {
    try {
      final XFile? file = await _picker.pickImage(source: ImageSource.gallery);
      if (file == null) return;
      
      final bytes = await file.readAsBytes();
      setState(() {
        _displayImageBytes = bytes;
        _inferenceStatus = "Decoding JPEG pixels and scaling for WASM Matrix...";
      });

      // Decode image bytes into an RGB pixel map
      final originalImage = img.decodeImage(bytes);
      if (originalImage == null) throw Exception("Failed to decode X-Ray image.");
      
      // Scale to 512x512 matrix shape that our TFJS WASM model expects
      final resizedImage = img.copyResize(originalImage, width: 512, height: 512);
      
      // Convert to normalized Float32 array (RGB) for TFLite WASM backend ingestion
      final float32List = Float32List(512 * 512 * 3);
      int bufferIndex = 0;
      for (final pixel in resizedImage) {
        float32List[bufferIndex++] = pixel.r / 255.0;
        float32List[bufferIndex++] = pixel.g / 255.0;
        float32List[bufferIndex++] = pixel.b / 255.0;
      }
      
      setState(() => _inferenceStatus = "Executing Native WASM Float32 TFLite Inference...");
      
      // Pass the genuine physical pixel array into the WASM AI layer!
      final actualScore = await _inferenceEngine.runOnDeviceInference(float32List.buffer.asUint8List());
      
      setState(() => _inferenceStatus = "[SUCCESS] Genuine Pixels Analyzed! Triage AI Score: ${actualScore.toStringAsFixed(2)}");
    } catch (e) {
      setState(() => _inferenceStatus = "[ERROR] Pixel ingestion failed: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Diagnostic Review Matrix (Real Image Data)', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 20),
          Container(
            height: 400,
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.black87,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: _displayImageBytes != null 
                ? Image.memory(_displayImageBytes!, fit: BoxFit.contain)
                : Text('No Image Loaded', style: TextStyle(color: Colors.grey[500])),
            ),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: _pickAndAnalyzeImage,
            icon: const Icon(Icons.file_upload),
            label: const Text('Upload Real X-Ray & Execute Edge AI'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _inferenceStatus,
            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blueAccent, fontSize: 16),
          ),
        ],
      ),
    );
  }
}
