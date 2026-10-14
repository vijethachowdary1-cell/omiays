"""
AlphabetAI Attendance - SQLite Database Layer
Handles student rosters, biometric descriptor metadata, attendance records, and audit logs.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "alphabetai.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT NOT NULL,
            section TEXT NOT NULL,
            avatar_url TEXT,
            face_descriptor TEXT,  -- JSON string of biometric embeddings
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Attendance records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late', 'Excused')),
            time_marked TEXT,
            confidence REAL DEFAULT 0.0,
            verified_by_teacher INTEGER DEFAULT 0,
            method TEXT DEFAULT 'AI_FACE',
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(student_id, date)
        )
    """)

    # Audit logs for teacher manual overrides
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            teacher_name TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            reason TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()

    # Seed initial demo students if table is empty
    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_students = [
            ("CS2026-001", "Aarav Sharma", "aarav@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"),
            ("CS2026-002", "Ananya Verma", "ananya@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150"),
            ("CS2026-003", "Bhavya Patel", "bhavya@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150"),
            ("CS2026-004", "Chirag Reddy", "chirag@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"),
            ("CS2026-005", "Diya Mukherjee", "diya@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150"),
            ("CS2026-006", "Eshan Gupta", "eshan@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"),
            ("CS2026-007", "Farhan Akhtar", "farhan@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150"),
            ("CS2026-008", "Gauri Deshmukh", "gauri@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150"),
            ("CS2026-009", "Harshvardhan Rao", "harsh@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150"),
            ("CS2026-010", "Ishita Sengupta", "ishita@alphabetai.edu", "Computer Science", "A", "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150")
        ]
        for roll, name, email, dept, sec, avatar in seed_students:
            cursor.execute("""
                INSERT INTO students (roll_no, name, email, department, section, avatar_url, face_descriptor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (roll, name, email, dept, sec, avatar, json.dumps([0.1] * 128)))
        conn.commit()

        # Seed today's initial attendance
        today = datetime.now().strftime("%Y-%m-%d")
        for i in range(1, 11):
            status = 'Present' if i in [1, 2, 3, 5, 6, 8, 10] else ('Late' if i == 4 else 'Absent')
            time_str = "09:05:12" if status == 'Present' else ("09:22:45" if status == 'Late' else None)
            cursor.execute("""
                INSERT INTO attendance (student_id, date, status, time_marked, confidence, verified_by_teacher, method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (i, today, status, time_str, 0.94 if status != 'Absent' else 0.0, 1 if status == 'Present' else 0, 'AI_FACE'))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("AlphabetAI Attendance Database initialized successfully.")
