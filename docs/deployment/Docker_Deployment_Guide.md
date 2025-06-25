# RAGTrace Docker 배포 가이드

이 문서는 RAGTrace를 Docker 이미지를 사용하여 리눅스 VM이나 서버에 배포하는 방법을 설명합니다.

## 목차
- [빠른 시작](#빠른-시작)
- [사전 요구사항](#사전-요구사항)
- [배포 방법](#배포-방법)
- [설정 옵션](#설정-옵션)
- [문제 해결](#문제-해결)

## 빠른 시작

### 1분 안에 RAGTrace 실행하기

```bash
# 1. Docker 이미지 다운로드
docker pull ghcr.io/ntts9990/ragtrace:latest

# 2. API 키를 포함하여 실행
docker run -d \
  -p 8501:8501 \
  -e GEMINI_API_KEY="your-gemini-api-key" \
  -v $(pwd)/data:/app/data \
  --name ragtrace \
  ghcr.io/ntts9990/ragtrace:latest

# 3. 브라우저에서 접속
# http://your-server-ip:8501
```

## 사전 요구사항

### 필수 요구사항
- Docker 20.10+ 또는 Docker Engine
- 최소 2GB RAM (권장 4GB+)
- 최소 5GB 디스크 공간
- 포트 8501 사용 가능

### API 키 준비
- **필수**: Google Gemini API Key ([획득하기](https://aistudio.google.com/app/apikey))
- **선택**: Naver CLOVA Studio API Key (HCX 모델 사용시)

## 배포 방법

### 방법 1: Docker Run (간단한 실행)

```bash
# 기본 실행
docker run -d \
  --name ragtrace \
  -p 8501:8501 \
  -e GEMINI_API_KEY="your-api-key" \
  -v $(pwd)/data:/app/data \
  ghcr.io/ntts9990/ragtrace:latest

# 모든 옵션 포함 실행
docker run -d \
  --name ragtrace \
  -p 8501:8501 \
  -e GEMINI_API_KEY="your-gemini-key" \
  -e CLOVA_STUDIO_API_KEY="your-clova-key" \
  -e DEFAULT_LLM="gemini" \
  -e DEFAULT_EMBEDDING="bge_m3" \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/models:/app/models \
  --restart unless-stopped \
  ghcr.io/ntts9990/ragtrace:latest
```

### 방법 2: Docker Compose (권장)

#### 1. docker-compose.yml 다운로드
```bash
# GitHub에서 직접 다운로드
wget https://raw.githubusercontent.com/ntts9990/RAGTrace/main/docker-compose.yml

# 또는 curl 사용
curl -O https://raw.githubusercontent.com/ntts9990/RAGTrace/main/docker-compose.yml
```

#### 2. 환경 설정 파일 생성
```bash
# .env 파일 생성
cat > .env << EOF
# 필수 API 키
GEMINI_API_KEY=your-gemini-api-key

# 선택 API 키 (HCX 모델 사용시)
CLOVA_STUDIO_API_KEY=your-clova-api-key

# 기본 모델 설정
DEFAULT_LLM=gemini
DEFAULT_EMBEDDING=bge_m3
EOF
```

#### 3. 서비스 실행
```bash
# 웹 대시보드 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# 서비스 상태 확인
docker compose ps
```

### 방법 3: 프로덕션 배포 (SystemD)

#### 1. SystemD 서비스 파일 생성
```bash
sudo tee /etc/systemd/system/ragtrace.service << EOF
[Unit]
Description=RAGTrace RAG Evaluation Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
Environment="GEMINI_API_KEY=your-api-key"
ExecStartPre=-/usr/bin/docker stop ragtrace
ExecStartPre=-/usr/bin/docker rm ragtrace
ExecStartPre=/usr/bin/docker pull ghcr.io/ntts9990/ragtrace:latest
ExecStart=/usr/bin/docker run --rm --name ragtrace \
  -p 8501:8501 \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -v /var/lib/ragtrace/data:/app/data \
  ghcr.io/ntts9990/ragtrace:latest
ExecStop=/usr/bin/docker stop ragtrace

[Install]
WantedBy=multi-user.target
EOF
```

#### 2. 서비스 시작
```bash
# 데이터 디렉토리 생성
sudo mkdir -p /var/lib/ragtrace/data

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable ragtrace
sudo systemctl start ragtrace

# 상태 확인
sudo systemctl status ragtrace
```

## 설정 옵션

### 환경 변수

| 변수명 | 설명 | 필수 | 기본값 |
|--------|------|------|--------|
| `GEMINI_API_KEY` | Google Gemini API 키 | ✅ | - |
| `CLOVA_STUDIO_API_KEY` | Naver CLOVA Studio API 키 | ❌ | - |
| `DEFAULT_LLM` | 기본 LLM 모델 | ❌ | gemini |
| `DEFAULT_EMBEDDING` | 기본 임베딩 모델 | ❌ | gemini |
| `STREAMLIT_SERVER_PORT` | 웹 서버 포트 | ❌ | 8501 |

### 볼륨 마운트

| 호스트 경로 | 컨테이너 경로 | 설명 |
|------------|--------------|------|
| `./data` | `/app/data` | 평가 데이터 및 결과 |
| `./models` | `/app/models` | BGE-M3 로컬 모델 (선택) |

### 포트 매핑

- `8501`: Streamlit 웹 대시보드

## 플랫폼별 이미지

Docker는 자동으로 적절한 플랫폼 이미지를 선택합니다:

- **linux/amd64**: Intel/AMD x86_64 서버
- **linux/arm64**: ARM64 서버 (AWS Graviton, Apple Silicon 등)

## 접속 및 사용

### 웹 대시보드 접속
```
http://your-server-ip:8501
```

### CLI 사용 (컨테이너 내부)
```bash
# 컨테이너 접속
docker exec -it ragtrace bash

# CLI 평가 실행
uv run python cli.py evaluate evaluation_data.json
```

## 문제 해결

### 이미지 Pull 실패
```bash
# GitHub Container Registry 로그인
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 수동으로 이미지 다운로드
docker pull ghcr.io/ntts9990/ragtrace:latest
```

### 포트 충돌
```bash
# 8501 포트 사용 중인 프로세스 확인
sudo lsof -i :8501

# 다른 포트로 실행
docker run -p 8502:8501 ...
```

### 메모리 부족
```bash
# Docker 리소스 제한 설정
docker run -m 4g --memory-swap 4g ...
```

### 로그 확인
```bash
# 실시간 로그
docker logs -f ragtrace

# 최근 100줄
docker logs --tail 100 ragtrace
```

### 컨테이너 재시작
```bash
# 재시작
docker restart ragtrace

# 강제 재생성
docker stop ragtrace
docker rm ragtrace
docker run ... # 다시 실행
```

## 보안 고려사항

### 프로덕션 환경 권장사항

1. **환경 변수 보호**
   ```bash
   # Docker Secrets 사용 (Swarm mode)
   echo "your-api-key" | docker secret create gemini_api_key -
   ```

2. **네트워크 격리**
   ```bash
   # 내부 네트워크만 사용
   docker run --network internal ...
   ```

3. **리버스 프록시 설정** (Nginx 예시)
   ```nginx
   server {
       listen 443 ssl;
       server_name ragtrace.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 모니터링

### 헬스체크
```bash
# 헬스 상태 확인
curl http://localhost:8501/_stcore/health

# Docker 헬스 상태
docker inspect ragtrace --format='{{.State.Health.Status}}'
```

### 리소스 사용량
```bash
# CPU/메모리 사용량
docker stats ragtrace

# 디스크 사용량
docker system df
```

## 업데이트

### 최신 버전으로 업데이트
```bash
# 1. 현재 컨테이너 중지
docker stop ragtrace

# 2. 최신 이미지 다운로드
docker pull ghcr.io/ntts9990/ragtrace:latest

# 3. 기존 컨테이너 삭제
docker rm ragtrace

# 4. 새 버전으로 실행
docker run -d --name ragtrace ... ghcr.io/ntts9990/ragtrace:latest
```

### Docker Compose 업데이트
```bash
# 최신 이미지로 업데이트하고 재시작
docker compose pull
docker compose up -d
```

## 백업 및 복구

### 데이터 백업
```bash
# 평가 데이터 백업
docker run --rm \
  -v ragtrace_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/ragtrace-backup-$(date +%Y%m%d).tar.gz /data
```

### 데이터 복구
```bash
# 백업에서 복구
docker run --rm \
  -v ragtrace_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/ragtrace-backup-20240122.tar.gz -C /
```

## 도움말

### 추가 정보
- [RAGTrace GitHub Repository](https://github.com/ntts9990/RAGTrace)
- [Docker Hub 이미지](https://ghcr.io/ntts9990/ragtrace)
- [문제 신고](https://github.com/ntts9990/RAGTrace/issues)

### 지원 플랫폼
- Ubuntu 20.04+
- CentOS 8+
- Debian 11+
- Amazon Linux 2
- 기타 Docker 지원 Linux 배포판