# ExamGuard — AI-Proctored Examination Platform

A production-ready, full-stack online examination platform with integrated real-time AI proctoring, built on React, FastAPI, SQLite/PostgreSQL, OpenCV, MediaPipe, and YOLOv8.

---

## 🏗 Architecture Overview

```
exam_platform/
├── frontend/              # React 18 + TailwindCSS + Vite
│   └── src/
│       ├── pages/         # Teacher dashboard, exam page, results, live monitor
│       ├── components/    # Reusable UI components
│       ├── contexts/      # Auth context (JWT)
│       └── utils/         # Axios API client
│
├── backend/               # FastAPI (Python 3.11)
│   ├── main.py            # App entry point + WebSocket manager
│   ├── routers/           # auth / tests / questions / submissions / proctoring / results
│   ├── models/            # SQLAlchemy ORM models
│   └── database/          # SQLite/PostgreSQL engine
│
├── ai_proctoring/         # CV pipeline (from your uploaded module)
│   ├── detection/         # face_detection, phone_detection, eye_tracking, head_pose, talking
│   ├── engine/            # frame_processor, scoring_engine
│   ├── utils/             # logger, evidence, video_recorder
│   └── model_loader.py    # Loads MediaPipe + YOLOv8
│
├── storage/
│   ├── evidence/          # Captured violation screenshots / clips
│   └── logs/              # CSV violation logs
│
├── docker-compose.yml
└── start.sh               # One-command local dev startup
```

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### One-command startup
```bash
chmod +x start.sh
./start.sh
```

Then open:
- **Teacher Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Demo credentials (auto-seeded)
| Role    | Email                | Password  |
|---------|----------------------|-----------|
| Teacher | teacher@demo.com     | demo1234  |
| Student | student@demo.com     | demo1234  |

---

## 📦 Manual Setup

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Seed demo data
PYTHONPATH=.:../ai_proctoring python seed.py

# Run dev server
PYTHONPATH=.:../ai_proctoring uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- API: http://localhost:8000

---

## 🎯 Core Features

### Teacher Dashboard
| Feature | Details |
|---------|---------|
| Create Tests | Title, description, duration, marks, date/time window |
| Unique Test Links | `https://platform.com/test/ABC12345` |
| Question Editor | MCQ, Multi-select, Short Answer, Coding |
| Question Reorder | Drag-and-drop ordering |
| Results Table | Score, integrity score, risk level, violations |
| Violation Timeline | Per-student chronological event log |
| Evidence Gallery | Screenshots captured during violations |
| Live Monitor | Real-time webcam grid with violation alerts |

### Student Exam Interface
| Feature | Details |
|---------|---------|
| Test Entry | Access code → Login → Instructions → Camera check |
| Proctored Exam | Webcam feed, timer, question panel, auto-save |
| Question Navigator | Visual grid showing answered/flagged/current |
| Integrity Score | Live score shown during exam |
| Auto-submission | Timer expiry triggers automatic submission |

### AI Proctoring (Real-time)
| Detection | Method | Trigger |
|-----------|--------|---------|
| Face Detection | MediaPipe Face Detection | No face / Multiple faces |
| Head Pose | MediaPipe Face Mesh landmarks | Looking away > 2.5s |
| Eye Gaze | Iris landmark tracking | Left/Right/Up/Down gaze |
| Mouth / Talking | Lip distance ratio | Mouth opening detected |
| Phone Detection | YOLOv8 (COCO class 67) | Phone visible on camera |
| Laptop Detection | YOLOv8 (COCO class 63) | Secondary device on camera |
| Tab Switch | `visibilitychange` + `blur` events | Tab hidden / window unfocused |
| Copy/Paste | `copy`, `paste`, `cut` event blocking | Attempt logged and blocked |
| Fullscreen | Fullscreen API enforcement | Exit triggers re-entry prompt |
| Network Drop | `offline` event | Disconnect logged |

### Integrity Score System
```
Start: 100 points
Phone detected:      −30
Multiple faces:      −50
No face:             −15
Tab switched:        −15
Looking away (head): −10
Eye gaze away:       −8
Talking detected:    −8
Fullscreen exit:     −10
Laptop detected:     −25

Risk levels:
  ≥80  → Low Risk    (green)
  ≥50  → Medium Risk (amber)
  <50  → High Risk   (red)
```

### Auto-Grading
- **MCQ**: Exact match → full marks
- **Multi-select**: All correct options selected → full marks
- **Short Answer / Coding**: Stored for manual teacher review

---

## 🔐 Security

- JWT authentication (24h expiry)
- Password hashing via bcrypt
- Role-based access control (teacher / student / admin)
- Unique per-test access codes
- Copy-paste blocked in exam
- Fullscreen enforcement
- WebSocket rooms scoped per test

---

## 📡 API Reference

Full interactive docs at: `http://localhost:8000/docs`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Get JWT token |
| `/api/tests/` | GET/POST | List / create tests |
| `/api/tests/{id}` | GET/PUT/DELETE | Manage test |
| `/api/tests/code/{code}` | GET | Get test by access code |
| `/api/questions/` | POST | Add question |
| `/api/questions/test/{id}` | GET | Get questions (teacher) |
| `/api/questions/student/test/{id}` | GET | Get questions (no answers) |
| `/api/submissions/start` | POST | Start exam session |
| `/api/submissions/{id}/save-answer` | POST | Auto-save answer |
| `/api/submissions/{id}/submit` | POST | Final submission + grading |
| `/api/proctoring/violation` | POST | Log a violation |
| `/api/proctoring/analyze-frame` | POST | AI frame analysis |
| `/api/results/test/{id}` | GET | Test result summary |
| `/api/results/submission/{id}/detail` | GET | Full submission detail |
| `/ws/proctor/{test_id}/{student_id}` | WS | Student → server feed |
| `/ws/teacher/{test_id}` | WS | Teacher live monitor |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./examguard.db` | Database connection string |
| `SECRET_KEY` | (hardcoded dev key) | JWT signing key — **change in production** |
| `VITE_API_URL` | (empty — uses Vite proxy) | Backend URL for production |

### PostgreSQL (production)
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/examguard uvicorn main:app
```

---

## 📁 AI Proctoring Integration

The `ai_proctoring/` directory contains your uploaded CV module. It integrates into the backend via:

1. **REST endpoint** (`/api/proctoring/analyze-frame`): Student webcam frames (base64 JPEG) are sent every 5 seconds. The backend decodes them, runs the full `process_frame()` pipeline, and logs any violations.

2. **Frame processor**: `engine/frame_processor.py` → runs face detection, head pose, eye tracking, talking detection, and YOLOv8 phone detection in sequence.

3. **Scoring engine**: `engine/scoring_engine.py` → persist-threshold logic (violation must last >2.5s before penalty), cooldown timers, and final report generation.

### Running standalone (original Streamlit UI)
```bash
cd ai_proctoring
pip install -r requirements.txt
streamlit run app.py
```

---

## 🗂 Database Schema

```
users            → id, email, username, full_name, role, hashed_password
tests            → id, title, access_code, duration_mins, total_marks, creator_id
questions        → id, test_id, question_text, question_type, options, correct_answer, marks
submissions      → id, test_id, student_id, score, integrity_score, risk_level
answers          → id, submission_id, question_id, selected_options, marks_awarded
violation_logs   → id, submission_id, violation_type, confidence_score, evidence_path, penalty
```

---

## 🎨 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend UI | React 18, TailwindCSS, Vite |
| Routing | React Router v6 |
| Charts | Recharts |
| Backend | FastAPI, Python 3.11 |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | SQLAlchemy + SQLite (swap to PostgreSQL) |
| WebSocket | FastAPI native WebSockets |
| Face/Mesh | MediaPipe |
| Object Detection | YOLOv8 (Ultralytics) |
| Frame CV | OpenCV |
| Deployment | Docker + Nginx |

---

## 📝 License

MIT — free to use, modify, and deploy.
