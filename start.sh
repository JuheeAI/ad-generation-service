#!/bin/bash

# 1. 환경 변수 설정
export API_BASE="http://127.0.0.1:9000"
export HF_HOME="/workspace/huggingface"

# .env 파일 로드 (있으면)
if [ -f .env ]; then
  export $(cat .env | xargs)
fi

echo "--- 🚀 서비스 시작 ---"

# 2. 백엔드 실행 (로그는 backend.log에 저장)
echo "backend: Starting FastAPI on port 9000..."
nohup uvicorn src.backend.main:app --host 0.0.0.0 --port 9000 > backend.log 2>&1 &
BACKEND_PID=$!

# 백엔드 로딩 대기 (10초 정도 넉넉히)
echo "Waiting for backend to initialize..."
sleep 10

# 3. 프론트엔드 실행 (로그는 frontend.log에 저장)
echo "frontend: Starting Streamlit on port 8501..."
nohup streamlit run src/frontend/app.py --server.port 8501 --server.address 0.0.0.0 > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "--- ✅ 모든 서비스가 실행되었습니다 ---"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "---------------------------------------------------"
echo "📝 로그 확인 명령어:"
echo "  tail -f backend.log"
echo "  tail -f frontend.log"
echo "🛑 종료 명령어:"
echo "  pkill -f uvicorn && pkill -f streamlit"
echo "---------------------------------------------------"
