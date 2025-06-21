#!/bin/bash

# Docker Test Script for RAGTrace
# This script tests the Docker setup locally

set -e

echo "🐳 RAGTrace Docker 테스트 스크립트"
echo "=================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다. Docker Desktop을 시작해주세요."
    exit 1
fi

echo "✅ Docker가 실행 중입니다."

# Create test .env file
echo "📝 테스트용 .env 파일 생성..."
cat > .env.test << 'EOF'
GEMINI_API_KEY=test_key_for_docker_build
CLOVA_STUDIO_API_KEY=test_key_for_docker_build
DEFAULT_LLM=gemini
POSTGRES_PASSWORD=test_password
EOF

# Test Docker build
echo "🔨 Docker 이미지 빌드 테스트..."
docker build -t ragtrace:test .

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 성공"
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

# Test basic container run
echo "🚀 컨테이너 기본 실행 테스트..."
docker run --rm \
    --env-file .env.test \
    ragtrace:test uv run python hello.py

if [ $? -eq 0 ]; then
    echo "✅ 컨테이너 기본 실행 성공"
else
    echo "❌ 컨테이너 기본 실행 실패"
    exit 1
fi

# Test docker-compose build
echo "🏗️  Docker Compose 빌드 테스트..."
cp .env.test .env
docker-compose build ragtrace

if [ $? -eq 0 ]; then
    echo "✅ Docker Compose 빌드 성공"
else
    echo "❌ Docker Compose 빌드 실패"
    exit 1
fi

# Test CLI service
echo "⚡ CLI 서비스 테스트..."
docker-compose run --rm ragtrace-cli uv run python hello.py

if [ $? -eq 0 ]; then
    echo "✅ CLI 서비스 테스트 성공"
else
    echo "❌ CLI 서비스 테스트 실패"
    exit 1
fi

# Cleanup
echo "🧹 정리 중..."
rm -f .env.test .env
docker image prune -f

echo "🎉 모든 Docker 테스트가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 실제 API 키로 .env 파일 생성"
echo "2. docker-compose up -d ragtrace 로 서비스 시작"
echo "3. http://localhost:8501 에서 대시보드 확인"