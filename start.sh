#!/usr/bin/env bash
# ── start.sh — Local development startup ─────────────────────────────────────
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   ExamGuard AI Proctoring Platform    ║"
echo "  ║          Development Setup             ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Backend setup ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Setting up Python backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "  ✓ Dependencies installed"

python seed.py
echo "  ✓ Database seeded"

# Start backend in background
PYTHONPATH="$(pwd):$(pwd)/../ai_proctoring" uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}  ✓ Backend running on http://localhost:8000  (PID: $BACKEND_PID)${NC}"

cd ..

# ── Frontend setup ────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/4] Setting up React frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
fi
echo "  ✓ Node modules ready"

npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}  ✓ Frontend running on http://localhost:3000  (PID: $FRONTEND_PID)${NC}"

cd ..

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 ExamGuard is running!${NC}"
echo ""
echo "  📖 Teacher Dashboard  →  http://localhost:3000"
echo "  📡 API Docs (Swagger) →  http://localhost:8000/docs"
echo "  📡 API Docs (ReDoc)   →  http://localhost:8000/redoc"
echo ""
echo "  Demo Accounts:"
echo "    Teacher: teacher@demo.com / demo1234"
echo "    Student: student@demo.com / demo1234"
echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait and cleanup on exit
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
