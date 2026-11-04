"""
Subsystem 11: Production History & SQLite Audit Database
-------------------------------------------------------
Tracks all film projects, scenes, shots, asset registries, render histories,
and 10-tier automated quality control audit records.
"""

import sqlite3
import json
import time
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = STUDIO_ROOT / "reports" / "production_studio.db"

def init_database(db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    # Assets Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        filepath TEXT NOT NULL,
        file_size_bytes INTEGER,
        metadata_json TEXT,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'VERIFIED'
    )
    """)

    # Shots & Scenes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        scene_name TEXT NOT NULL,
        shot_number INTEGER NOT NULL,
        description TEXT,
        frame_start INTEGER NOT NULL,
        frame_end INTEGER NOT NULL,
        fps INTEGER DEFAULT 30,
        status TEXT DEFAULT 'PENDING',
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )
    """)

    # QC Audits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qc_audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shot_id INTEGER,
        module_name TEXT NOT NULL,
        status TEXT NOT NULL,
        details_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(shot_id) REFERENCES shots(id)
    )
    """)

    # Renders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS renders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shot_id INTEGER,
        render_type TEXT NOT NULL,
        output_path TEXT NOT NULL,
        resolution TEXT NOT NULL,
        file_size_bytes INTEGER,
        render_time_seconds REAL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(shot_id) REFERENCES shots(id)
    )
    """)

    conn.commit()
    conn.close()
    print(f"[DATABASE READY] Initialized SQLite studio database at {db_path}")

def record_render_event(shot_name, render_type, output_path, resolution, file_size, render_time, status="PASS", db_path=DB_PATH):
    init_database(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO renders (render_type, output_path, resolution, file_size_bytes, render_time_seconds, created_at, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (render_type, str(output_path), resolution, file_size, render_time, now, status))
    
    conn.commit()
    conn.close()

def record_qc_audit(module_name, status, details, db_path=DB_PATH):
    init_database(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO qc_audits (module_name, status, details_json, created_at)
    VALUES (?, ?, ?, ?)
    """, (module_name, status, json.dumps(details), now))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
