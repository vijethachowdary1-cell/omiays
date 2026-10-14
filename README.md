# AlphabetAI Attendance 🚀

> **AI-Powered Mobile-First Smart Attendance System** with live face recognition, A–Z and roll-number sorting, teacher verification, and biometric privacy.

---

## 🌟 Key Features

- **📱 Mobile-Friendly Live Camera Scanner:**
  - Front / Rear camera switching for mobile phone classroom scanning.
  - Real-time facial bounding box HUD overlay with liveness target guide.
  - Zero-latency Web Audio API chime synthesis on successful mark.
  - Smart deduplication to prevent accidental double marks.

- **🎓 Student Registration & Smart Sorting:**
  - Onboard students with multi-angle face capture and metadata.
  - **A–Z / Z–A Alphabetical Sorting** by student name.
  - **Natural Roll Number Sorting** (e.g., `CS-1`, `CS-2`, `CS-10`).
  - Instant live search by name or roll number.
  - 1-Click quick status toggles (`Present`, `Late`, `Absent`, `Excused`).

- **🔐 Teacher Verification & Audit Logging:**
  - Teacher sign-off mode to review auto-detected attendance before locking.
  - Manual overrides with mandatory reason logging for compliance.
  - Immutable audit trail tracking who changed what and when.

- **📊 Reports & Data Privacy:**
  - Daily summary statistics with dynamic attendance percentage rates.
  - Instant **CSV Export** and print-ready report generation.
  - **Biometric Privacy Guarantee:** Facial features stored as non-reversible numerical vector embeddings, keeping raw images secure.

---

## 🚀 Quick Start (Zero Dependencies)

The core backend uses Python's built-in standard library (`http.server` + `sqlite3`), requiring **no complex external installation**.

### 1. Clone & Navigate
```bash
git clone https://github.com/vijethachowdary1-cell/aiapp.git
cd aiapp
```

### 2. Start the Server
```bash
python app.py
```
*(Or use `py app.py` on Windows)*

### 3. Open in Browser
Visit **[http://localhost:8000](http://localhost:8000)** on your laptop or mobile browser.

---

## 🐳 Docker Deployment

To run containerized anywhere (AWS, GCP, DigitalOcean, Render, Railway):

```bash
docker build -t alphabetai-attendance .
docker run -p 8000:8000 alphabetai-attendance
```

---

## 📂 Project Structure

```
├── app.py              # REST API & static file HTTP server
├── database.py         # SQLite schema & seed database layer
├── index.html          # Mobile-first responsive Tailwind web app
├── static/
│   └── js/
│       └── app.js      # Camera HUD, live detection, and sorting logic
├── requirements.txt    # Optional advanced package references
├── Dockerfile          # Production Docker container definition
└── .gitignore          # Clean version control configuration
```

---

## 📄 License
MIT License. Built for educational and institutional attendance automation.
