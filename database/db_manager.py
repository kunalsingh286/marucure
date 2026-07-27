import sqlite3
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a configured database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA cache_size = -64000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def initialize_database(self, schema_path: str):
        """Initialize the database using the schema file."""
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_script = f.read()

        try:
            conn = self.get_connection()
            with conn:
                cursor = conn.cursor()
                # Execute the full script including PRAGMAs and CREATE TABLE statements
                cursor.executescript(schema_script)
            logger.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def insert_miner(self, jan_aadhaar_no: str, full_name: str, age: int, gender: str, exposure_years: float, occupation_type: str):
        """Insert a new miner profile."""
        query = '''
            INSERT INTO local_miners (jan_aadhaar_no, full_name, age, gender, exposure_years, occupation_type)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            # Enforce pragmas per connection as they are not always persisted across all connections 
            # (especially foreign_keys which is off by default in sqlite3)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute(query, (jan_aadhaar_no, full_name, age, gender, exposure_years, occupation_type))
            conn.commit()
            logger.info(f"Successfully inserted miner {jan_aadhaar_no}")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to insert miner: {e}")
            raise
        finally:
            conn.close()

    def log_screening(self, jan_aadhaar_no: str, spirometry_fev1_fvc: float, ai_confidence_score: float, calculated_risk_index: float, local_image_path: str) -> str:
        """Log an individual offline screening session. Returns the generated screening UUID."""
        screening_id = str(uuid.uuid4())
        query = '''
            INSERT INTO local_screenings (screening_id, jan_aadhaar_no, spirometry_fev1_fvc, ai_confidence_score, calculated_risk_index, local_image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute(query, (screening_id, jan_aadhaar_no, spirometry_fev1_fvc, ai_confidence_score, calculated_risk_index, local_image_path))
            conn.commit()
            logger.info(f"Successfully logged screening {screening_id} for miner {jan_aadhaar_no}")
            return screening_id
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to log screening: {e}")
            raise
        finally:
            conn.close()

    def get_unsynced_records(self):
        """Retrieve a batch of all records where sync_status = 0."""
        query = '''
            SELECT s.*, m.full_name, m.age, m.gender, m.exposure_years, m.occupation_type
            FROM local_screenings s
            JOIN local_miners m ON s.jan_aadhaar_no = m.jan_aadhaar_no
            WHERE s.sync_status = 0
        '''
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            # Fetch as dicts
            records = [dict(row) for row in cursor.fetchall()]
            return records
        except sqlite3.Error as e:
            logger.error(f"Failed to fetch unsynced records: {e}")
            raise
        finally:
            conn.close()

    def insert_screening_batch(self, records_list):
        """Processes multiple screening entries concurrently before executing a unified atomic commit."""
        query = '''
            INSERT INTO local_screenings (screening_id, jan_aadhaar_no, spirometry_fev1_fvc, ai_confidence_score, calculated_risk_index, local_image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        conn = self.get_connection()
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            with conn: # strict atomic transaction block
                cursor.executemany(query, records_list)
            logger.info(f"Successfully processed atomic batch insert of {len(records_list)} screening records.")
        except sqlite3.Error as e:
            logger.error(f"Failed atomic batch processing: {e}")
            raise
        finally:
            conn.close()
