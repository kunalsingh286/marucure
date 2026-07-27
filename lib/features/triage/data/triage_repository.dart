import 'package:idb_shim/idb_browser.dart';
import 'package:idb_shim/idb.dart';
import '../domain/screening_entity.dart';

class TriageRepository {
  Database? _db;
  final String dbName = 'triage_local.db';
  final String storeName = 'screenings';

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    // Acquire the browser's native IndexedDB factory via idb_shim
    IdbFactory idbFactory = getIdbFactory()!;
    return await idbFactory.open(
      dbName,
      version: 1,
      onUpgradeNeeded: (VersionChangeEvent event) {
        Database db = event.database;
        db.createObjectStore(storeName, keyPath: 'id');
      },
    );
  }

  Future<void> insertScreening(ScreeningEntity entity) async {
    final db = await database;
    // Utilize atomic browser transaction crash-safety block
    var txn = db.transaction(storeName, 'readwrite');
    var store = txn.objectStore(storeName);
    await store.put(entity.toMap());
    await txn.completed;
  }

  Future<List<ScreeningEntity>> getAllScreenings() async {
    final db = await database;
    var txn = db.transaction(storeName, 'readonly');
    var store = txn.objectStore(storeName);
    
    List<ScreeningEntity> results = [];
    await store.openCursor(autoAdvance: true).listen((CursorWithValue cursor) {
      final map = Map<String, dynamic>.from(cursor.value as Map);
      results.add(ScreeningEntity.fromMap(map));
    }).asFuture();
    
    return results;
  }

  Future<List<ScreeningEntity>> getPendingScreenings() async {
    final all = await getAllScreenings();
    return all.where((e) => e.syncStatus == 'pending').toList();
  }

  Future<void> updateSyncStatus(String id, String newStatus) async {
    final db = await database;
    var txn = db.transaction(storeName, 'readwrite');
    var store = txn.objectStore(storeName);
    
    var record = await store.getObject(id);
    if (record != null) {
      var map = Map<String, dynamic>.from(record as Map);
      map['sync_status'] = newStatus;
      await store.put(map);
    }
    await txn.completed;
  }
}
