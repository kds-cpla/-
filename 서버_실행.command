#!/bin/bash

# 이 파일이 있는 폴더로 이동
cd "$(dirname "$0")"

echo "========================================="
echo "  노무법인 위민 - 사대보험 환급 서버 시작"
echo "========================================="
echo ""

# .env 파일 불러오기
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "✅ 환경변수 로드 완료"
else
  echo "❌ .env 파일이 없습니다. 먼저 .env 파일을 설정해주세요."
  read -p "아무 키나 누르면 종료됩니다..."
  exit 1
fi

# 패키지 설치
echo ""
echo "📦 필요한 패키지 설치 중..."
pip3 install -r requirements.txt -q

# 서버 실행
echo ""
echo "🚀 서버 시작! 브라우저에서 아래 주소로 접속하세요:"
echo ""
echo "   👉 http://localhost:8080"
echo ""
echo "서버를 종료하려면 이 창을 닫으세요."
echo "========================================="
echo ""

python3 server.py
