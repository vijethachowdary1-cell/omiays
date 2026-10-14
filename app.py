"""
AlphabetAI Attendance - Core Server & REST API
Built with Python standard library (http.server + sqlite3) for zero-dependency plug-and-play execution.
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import mimetypes
from datetime import datetime
import re

import database

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def natural_sort_key(s):
    """Sort strings with embedded numbers naturally (e.g. CS-2 before CS-10)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

class AlphabetAIHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and disable aggressive caching for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            return json.loads(body)
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static file routing
        if path == "/" or path == "":
            self.serve_file(os.path.join(BASE_DIR, "index.html"), "text/html")
            return
        elif not path.startswith("/api/"):
            file_path = os.path.join(BASE_DIR, path.lstrip("/"))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                self.serve_file(file_path, mime or "application/octet-stream")
                return
            else:
                self.send_error(404, "File Not Found")
                return

        # API Routes
        if path == "/api/students":
            self.handle_get_students(query)
        elif path == "/api/attendance":
            self.handle_get_attendance(query)
        elif path == "/api/stats":
            self.handle_get_stats(query)
        elif path == "/api/audit-logs":
            self.handle_get_audit_logs()
        elif path == "/api/export/csv":
            self.handle_export_csv(query)
        else:
            self.send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if path == "/api/students":
            self.handle_create_student(body)
        elif path == "/api/attendance/mark":
            self.handle_mark_attendance(body)
        elif path == "/api/attendance/override":
            self.handle_override_attendance(body)
        elif path == "/api/attendance/verify-all":
            self.handle_verify_all(body)
        else:
            self.send_json({"error": "Endpoint not found"}, 404)

    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Server error reading file: {e}")

    # ================= API Handlers =================

    def handle_get_students(self, query):
        sort_by = query.get("sort", ["name_asc"])[0]
        search = query.get("search", [""])[0].strip().lower()
        date_str = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]

        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.id, s.roll_no, s.name, s.email, s.department, s.section, s.avatar_url,
                   COALESCE(a.status, 'Absent') as attendance_status,
                   a.time_marked, a.confidence, a.verified_by_teacher, a.method
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
        """, (date_str,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        # Filtering
        if search:
            rows = [r for r in rows if search in r["name"].lower() or search in r["roll_no"].lower()]

        # Sorting logic: A-Z / Z-A or Natural Roll Number Sort
        if sort_by == "name_asc":
            rows.sort(key=lambda r: r["name"].lower())
        elif sort_by == "name_desc":
            rows.sort(key=lambda r: r["name"].lower(), reverse=True)
        elif sort_by == "roll_asc":
            rows.sort(key=lambda r: natural_sort_key(r["roll_no"]))
        elif sort_by == "roll_desc":
            rows.sort(key=lambda r: natural_sort_key(r["roll_no"]), reverse=True)
        elif sort_by == "status":
            order = {"Present": 0, "Late": 1, "Excused": 2, "Absent": 3}
            rows.sort(key=lambda r: order.get(r["attendance_status"], 4))

        self.send_json({"students": rows, "total": len(rows), "date": date_str})

    def handle_create_student(self, body):
        name = body.get("name", "").strip()
        roll_no = body.get("roll_no", "").strip().upper()
        email = body.get("email", "").strip()
        department = body.get("department", "Computer Science").strip()
        section = body.get("section", "A").strip()
        avatar_url = body.get("avatar_url") or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        face_descriptor = json.dumps(body.get("face_descriptor", [0.0] * 128))

        if not name or not roll_no:
            self.send_json({"error": "Name and Roll Number are required."}, 400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO students (roll_no, name, email, department, section, avatar_url, face_descriptor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (roll_no, name, email, department, section, avatar_url, face_descriptor))
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            self.send_json({"message": "Student registered successfully", "id": new_id, "roll_no": roll_no})
        except Exception as e:
            conn.close()
            self.send_json({"error": f"Failed to register student: {str(e)}"}, 400)

    def handle_mark_attendance(self, body):
        student_id = body.get("student_id")
        roll_no = body.get("roll_no")
        confidence = float(body.get("confidence", 0.95))
        method = body.get("method", "AI_FACE")
        date_str = body.get("date", datetime.now().strftime("%Y-%m-%d"))
        time_str = datetime.now().strftime("%H:%M:%S")

        conn = database.get_connection()
        cursor = conn.cursor()

        if not student_id and roll_no:
            cursor.execute("SELECT id FROM students WHERE roll_no = ?", (roll_no,))
            row = cursor.fetchone()
            if row:
                student_id = row["id"]

        if not student_id:
            conn.close()
            self.send_json({"error": "Valid student_id or roll_no required"}, 400)
            return

        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, time_marked, confidence, verified_by_teacher, method)
            VALUES (?, ?, 'Present', ?, ?, 0, ?)
            ON CONFLICT(student_id, date) DO UPDATE SET
                status='Present',
                time_marked=excluded.time_marked,
                confidence=excluded.confidence,
                method=excluded.method
        """, (student_id, date_str, time_str, confidence, method))
        conn.commit()
        conn.close()

        self.send_json({"message": "Attendance recorded", "student_id": student_id, "status": "Present", "time": time_str})

    def handle_override_attendance(self, body):
        student_id = body.get("student_id")
        date_str = body.get("date", datetime.now().strftime("%Y-%m-%d"))
        new_status = body.get("new_status")
        teacher_name = body.get("teacher_name", "Prof. Sharma")
        reason = body.get("reason", "Manual Teacher Adjustment")

        if not student_id or new_status not in ['Present', 'Absent', 'Late', 'Excused']:
            self.send_json({"error": "Valid student_id and status required"}, 400)
            return

        conn = database.get_connection()
        cursor = conn.cursor()

        # Get existing status
        cursor.execute("SELECT status FROM attendance WHERE student_id = ? AND date = ?", (student_id, date_str))
        row = cursor.fetchone()
        old_status = row["status"] if row else "Absent"

        # Update or insert
        time_str = datetime.now().strftime("%H:%M:%S")
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, time_marked, verified_by_teacher, method)
            VALUES (?, ?, ?, ?, 1, 'MANUAL_OVERRIDE')
            ON CONFLICT(student_id, date) DO UPDATE SET
                status=excluded.status,
                verified_by_teacher=1,
                method='MANUAL_OVERRIDE'
        """, (student_id, date_str, new_status, time_str))

        # Log audit trail
        cursor.execute("""
            INSERT INTO audit_logs (student_id, date, teacher_name, old_status, new_status, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, date_str, teacher_name, old_status, new_status, reason))

        conn.commit()
        conn.close()

        self.send_json({"message": "Status updated with audit log", "old_status": old_status, "new_status": new_status})

    def handle_verify_all(self, body):
        date_str = body.get("date", datetime.now().strftime("%Y-%m-%d"))
        teacher_name = body.get("teacher_name", "Prof. Sharma")

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE attendance SET verified_by_teacher = 1 WHERE date = ?", (date_str,))
        count = cursor.rowcount
        conn.commit()
        conn.close()

        self.send_json({"message": f"Verified {count} records for {date_str} by {teacher_name}"})

    def handle_get_stats(self, query):
        date_str = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]
        conn = database.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM attendance
            WHERE date = ?
            GROUP BY status
        """, (date_str,))
        counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        present = counts.get("Present", 0)
        late = counts.get("Late", 0)
        excused = counts.get("Excused", 0)
        absent = total_students - (present + late + excused)

        pct = round(((present + late) / total_students * 100), 1) if total_students > 0 else 0

        conn.close()
        self.send_json({
            "total_students": total_students,
            "present": present,
            "late": late,
            "absent": max(0, absent),
            "excused": excused,
            "attendance_rate": pct,
            "date": date_str
        })

    def handle_get_audit_logs(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.date, a.teacher_name, a.old_status, a.new_status, a.reason, a.timestamp,
                   s.name as student_name, s.roll_no
            FROM audit_logs a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.timestamp DESC
            LIMIT 50
        """)
        logs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        self.send_json({"audit_logs": logs})

    def handle_export_csv(self, query):
        date_str = query.get("date", [datetime.now().strftime("%Y-%m-%d")])[0]
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.roll_no, s.name, s.department, s.section,
                   COALESCE(a.status, 'Absent') as status,
                   COALESCE(a.time_marked, '--') as time_marked,
                   COALESCE(a.method, '--') as method,
                   COALESCE(a.verified_by_teacher, 0) as verified
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
            ORDER BY s.name ASC
        """, (date_str,))
        rows = cursor.fetchall()
        conn.close()

        csv_lines = ["Roll No,Student Name,Department,Section,Status,Time Marked,Method,Teacher Verified"]
        for r in rows:
            verified_str = "YES" if r["verified"] == 1 else "NO"
            csv_lines.append(f'"{r["roll_no"]}","{r["name"]}","{r["department"]}","{r["section"]}","{r["status"]}","{r["time_marked"]}","{r["method"]}","{verified_str}"')

        csv_content = "\r\n".join(csv_lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Disposition", f'attachment; filename="AlphabetAI_Attendance_{date_str}.csv"')
        self.send_header("Content-Length", str(len(csv_content)))
        self.end_headers()
        self.wfile.write(csv_content)

def run():
    database.init_db()
    with socketserver.ThreadingTCPServer(("", PORT), AlphabetAIHandler) as httpd:
        print(f"===========================================================")
        print(f"🚀 AlphabetAI Attendance Server Running at http://localhost:{PORT}")
        print(f"📱 Mobile-friendly web app & live scanner ready!")
        print(f"===========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run()
