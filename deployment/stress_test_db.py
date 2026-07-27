import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import uuid
from database.db_manager import DatabaseManager

def run_benchmark():
    db_path = 'stress_test.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = DatabaseManager(db_path)
    db.initialize_database('database/local_schema.sql')
    
    # insert 500 dummy miners so foreign keys pass
    miners = []
    for _ in range(500):
        ja = str(uuid.uuid4())[:12]
        db.insert_miner(ja, "Test Miner", 40, "M", 10.5, "stone_driller")
        miners.append(ja)
        
    # Prepare 500 screening records
    records = []
    for i in range(500):
        screening_id = str(uuid.uuid4())
        records.append((screening_id, miners[i], 0.75, 0.9, 8.5, f"/path/to/image_{i}.png"))
        
    start_time = time.time()
    db.insert_screening_batch(records)
    end_time = time.time()
    
    duration_ms = (end_time - start_time) * 1000
    print(f"[BENCHMARK] Python SQLite Batch Insert (500 records) took: {duration_ms:.2f} ms")
    if duration_ms < 15:
        print("[SUCCESS] Batch execution under 15ms threshold!")
    else:
        print("[WARNING] Execution exceeded 15ms threshold.")
        
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass

if __name__ == "__main__":
    run_benchmark()
