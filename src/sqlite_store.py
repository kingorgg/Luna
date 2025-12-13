import sqlite3
from pathlib import Path

from gi.repository import GLib


class SQLiteStore:
    def __init__(self, app_id: str):
        data_dir = Path(GLib.get_user_data_dir()) / app_id
        data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = data_dir / "luna.db"
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._init_schema()

    def _init_schema(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT UNIQUE NOT NULL,
                duration INTEGER NOT NULL,
                pregnancy_id TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS day_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                date TEXT UNIQUE NOT NULL,
                mood TEXT,
                temperature REAL,
                flow TEXT,
                notes TEXT,
                symptoms TEXT,
                FOREIGN KEY (cycle_id) REFERENCES cycles(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pregnancies (
                id TEXT PRIMARY KEY,
                start_date TEXT UNIQUE NOT NULL,
                confirmed INTEGER NOT NULL,
                end_date TEXT,
                notes TEXT,
                custom_due_date TEXT
            )
        """)

        self.conn.commit()
