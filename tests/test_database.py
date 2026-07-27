import unittest
import os
import sqlite3
import tempfile
from database.db_manager import DatabaseManager

class TestDatabaseArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a temporary file for the database
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix='.db')
        cls.schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'local_schema.sql')
        cls.db_manager = DatabaseManager(cls.db_path)
        
        # Initialize
        cls.db_manager.initialize_database(cls.schema_path)

    @classmethod
    def tearDownClass(cls):
        # Cleanup
        os.close(cls.db_fd)
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        # WAL creates auxiliary files
        if os.path.exists(cls.db_path + '-wal'):
            os.remove(cls.db_path + '-wal')
        if os.path.exists(cls.db_path + '-shm'):
            os.remove(cls.db_path + '-shm')

    def test_01_wal_mode_enabled(self):
        """Verify that WAL mode is successfully running."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(mode.lower(), 'wal', "Database is not in WAL mode!")

    def test_02_insert_mock_miner_and_screening(self):
        """Insert a mock miner, execute screening write sequence, and verify."""
        jan_aadhaar_no = "1234567890"
        
        # Insert miner
        self.db_manager.insert_miner(
            jan_aadhaar_no=jan_aadhaar_no,
            full_name="Rajesh Kumar",
            age=45,
            gender="M",
            exposure_years=12.5,
            occupation_type="stone_cutter"
        )
        
        # Log screening
        screening_id = self.db_manager.log_screening(
            jan_aadhaar_no=jan_aadhaar_no,
            spirometry_fev1_fvc=0.65,
            ai_confidence_score=0.92,
            calculated_risk_index=0.88,
            local_image_path="/path/to/mock/image.png"
        )
        self.assertIsNotNone(screening_id)
        
        # Retrieve and verify sync status is 0
        records = self.db_manager.get_unsynced_records()
        self.assertGreaterEqual(len(records), 1)
        
        found = False
        for rec in records:
            if rec['screening_id'] == screening_id:
                self.assertEqual(rec['sync_status'], 0)
                self.assertEqual(rec['full_name'], "Rajesh Kumar")
                found = True
                break
        self.assertTrue(found, "Newly inserted screening not found in unsynced records.")

    def test_03_constraint_checks(self):
        """Assert that constraint checks prevent bad data types/values from writing."""
        # 1. Invalid occupation type (CHECK constraint)
        with self.assertRaises(sqlite3.Error):
            self.db_manager.insert_miner(
                jan_aadhaar_no="0987654321",
                full_name="Invalid Miner",
                age=30,
                gender="M",
                exposure_years=5.0,
                occupation_type="software_engineer" # Invalid occupation
            )
            
        # 2. Invalid data type for age (should fail in STRICT mode)
        with self.assertRaises(sqlite3.Error):
            self.db_manager.insert_miner(
                jan_aadhaar_no="1122334455",
                full_name="String Age Miner",
                age="thirty", # String instead of integer
                gender="M",
                exposure_years=5.0,
                occupation_type="stone_driller"
            )

        # 3. Foreign key constraint
        with self.assertRaises(sqlite3.Error):
            self.db_manager.log_screening(
                jan_aadhaar_no="non_existent_aadhaar",
                spirometry_fev1_fvc=0.7,
                ai_confidence_score=0.5,
                calculated_risk_index=0.4,
                local_image_path="/path/to/invalid.png"
            )

if __name__ == '__main__':
    unittest.main()
