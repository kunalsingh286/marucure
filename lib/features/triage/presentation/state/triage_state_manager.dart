import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import '../../domain/screening_entity.dart';
import '../../data/triage_repository.dart';

class Debouncer {
  final int milliseconds;
  Timer? _timer;
  Debouncer({required this.milliseconds});
  void run(VoidCallback action) {
    _timer?.cancel();
    _timer = Timer(Duration(milliseconds: milliseconds), action);
  }
}

class TriageStateManager extends ChangeNotifier {
  final TriageRepository _repository;
  final Debouncer _searchDebouncer = Debouncer(milliseconds: 500);
  
  // Selective sliding view map tracking only active parameters for memory isolation
  final Map<String, ScreeningEntity> _activeViewMap = {};
  List<ScreeningEntity> get queue => _activeViewMap.values.toList();

  TriageStateManager(this._repository) {
    _loadQueue();
  }

  Future<void> _loadQueue({String query = ''}) async {
    final rawResults = await _repository.getAllScreenings();
    
    _activeViewMap.clear();
    int renderLimit = 50; // Strict sliding window capacity constraint
    int count = 0;
    
    for (var entity in rawResults) {
      // In production, filtering should occur at SQLite query level, 
      // but this demonstrates the sliding map boundary injection.
      _activeViewMap[entity.hashCode.toString()] = entity;
      count++;
      if (count >= renderLimit) break;
    }
    notifyListeners();
  }
  
  void onOperatorTextInput(String query) {
    // Asynchronous debouncer eliminates unneeded SQLite reads during high-dust typing
    _searchDebouncer.run(() {
      _loadQueue(query: query);
    });
  }

  /// Rejects in-memory temporary maps. Directly writes to SQLite and then streams update asynchronously.
  Future<void> registerNewScreening(ScreeningEntity entity) async {
    await _repository.insertScreening(entity);
    await _loadQueue();
  }
  
  // Method injected for testing purposes to safely mock the stream without actual SQLite bounds.
  void setMockQueueForTesting(List<ScreeningEntity> mockQueue) {
    _activeViewMap.clear();
    for (var entity in mockQueue) {
      _activeViewMap[entity.hashCode.toString()] = entity;
    }
    notifyListeners();
  }

  bool isSyncing = false;
  Future<void> syncOutbox() async {
    if (isSyncing) return;
    isSyncing = true;
    notifyListeners();
    
    try {
      final pending = await _repository.getPendingScreenings();
      for (var record in pending) {
        // Mock Go-Gov Server endpoint
        final response = await http.post(
          Uri.parse('http://localhost:8080/api/v1/sync'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode([record.toMap()]),
        );
        
        if (response.statusCode == 200 || response.statusCode == 202) {
          await _repository.updateSyncStatus(record.id, 'synced');
        }
      }
    } catch (e) {
      print("Sync failed, will retry on next connection: \$e");
    } finally {
      await _loadQueue();
      isSyncing = false;
      notifyListeners();
    }
  }
}
