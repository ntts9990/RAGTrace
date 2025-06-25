# RAGTrace 프로젝트 정리 계획

## 개요
Docker 워크플로 완료 후 새 브랜치를 생성하여 프로덕션에 필요한 핵심 파일들만 남기는 정리 작업 계획입니다.

## 사전 조건
- [ ] GitHub Actions의 모든 워크플로가 성공적으로 완료
- [ ] Docker 이미지가 정상적으로 빌드되고 push됨
- [ ] 모든 테스트가 통과함

## 작업 순서

### 1단계: 새 브랜치 생성 및 준비
```bash
# 1. 현재 상태 확인
git status
git log --oneline -5

# 2. 새 정리 브랜치 생성
git checkout -b cleanup/production-ready

# 3. 백업용 태그 생성 (만약을 위해)
git tag -a "v0.1.0-pre-cleanup" -m "Before cleanup: Full development version"
git push origin "v0.1.0-pre-cleanup"
```

### 2단계: 유지할 핵심 파일 목록 정의

#### 필수 유지 파일들
```
📁 프로젝트 루트
├── README.md                          # 프로젝트 소개
├── LICENSE                            # 라이선스
├── CLAUDE.md                          # Claude 가이드
├── pyproject.toml                     # 패키지 설정
├── uv.toml                           # UV 설정
├── uv.lock                           # 의존성 락
├── .python-version                    # Python 버전
├── Dockerfile                         # Docker 이미지
├── docker-compose.yml                 # Docker Compose
├── .dockerignore                      # Docker 무시 파일
├── .gitignore                        # Git 무시 파일
├── cli.py                            # CLI 진입점
├── hello.py                          # 연결 테스트
└── run_dashboard.py                   # 대시보드 실행

📁 .github/
└── workflows/
    ├── ci.yml                        # CI/CD 워크플로
    ├── docker-publish.yml            # Docker 빌드
    └── dependency-review.yml         # 의존성 리뷰

📁 src/ (전체 유지)
├── __init__.py
├── config.py                         # 설정
├── container.py                      # DI 컨테이너
├── domain/                           # 도메인 레이어
├── application/                      # 애플리케이션 레이어
├── infrastructure/                   # 인프라 레이어
├── presentation/                     # 프레젠테이션 레이어
└── utils/                           # 유틸리티

📁 data/
├── evaluation_data.json             # 샘플 데이터
├── evaluation_data_variant1.json    # 변형 데이터
└── db/ (디렉토리만)                  # DB 저장소

📁 docs/ (선별적)
├── Docker_Deployment_Guide.md       # Docker 배포 가이드
├── RAGTRACE_METRICS.md              # 메트릭 설명
└── Development_Guide.md             # 개발 가이드

📁 models/ (구조만)
└── bge-m3/ (디렉토리만, .gitkeep 추가)
```

#### 삭제 대상 파일들
```
📁 삭제할 파일들
├── data/
│   ├── test_data.json               # 테스트용 임시 데이터
│   └── invalid_data.json            # 테스트용 잘못된 데이터
├── docs/
│   ├── Functional_Test_Plan.md      # 개발용 테스트 계획
│   ├── Project_Cleanup_Plan.md      # 이 파일 (작업 완료 후)
│   ├── Architecture_And_Debugging_History.md
│   └── User_Scenario_Analysis.md    # 개발 과정 문서들
├── temp/ (전체)                     # 임시 파일들
├── htmlcov/ (전체)                  # 테스트 커버리지 리포트
├── scripts/ (전체)                  # 개발용 스크립트들
├── tests/ (선택적)                  # 테스트 파일들
├── performance_test.json            # 테스트 결과 파일
├── pytest.ini                      # 테스트 설정
├── justfile                        # 개발용 task runner
├── uv-setup.sh                     # 설치 스크립트
└── UV_SETUP.md                     # UV 설정 가이드
```

### 3단계: 실제 정리 작업

#### 3.1 불필요한 파일 삭제
```bash
# 테스트 관련 파일 삭제
rm -rf htmlcov/
rm -rf temp/
rm -rf scripts/
rm pytest.ini
rm justfile
rm uv-setup.sh
rm UV_SETUP.md

# 임시 데이터 파일 삭제
rm data/test_data.json
rm data/invalid_data.json
rm performance_test.json

# 개발 과정 문서 삭제
rm docs/Architecture_And_Debugging_History.md
rm docs/User_Scenario_Analysis.md
rm docs/Functional_Test_Plan.md

# tests/ 디렉토리 선택적 삭제 (운영에서 불필요시)
# rm -rf tests/
```

#### 3.2 필수 디렉토리 구조 유지
```bash
# 빈 디렉토리에 .gitkeep 추가
touch data/db/.gitkeep
touch data/temp/.gitkeep
touch models/bge-m3/.gitkeep

# Git에서 삭제된 파일들 스테이징
git add -A
```

#### 3.3 README.md 업데이트
```bash
# README.md에서 개발 관련 섹션 정리
# - 개발자용 내용 축소
# - 사용자 중심 내용으로 재구성
# - 설치 및 사용법에 집중
```

### 4단계: 검증 및 테스트

#### 4.1 기본 기능 테스트
```bash
# 기본 연결 테스트
uv run python hello.py

# CLI 기능 테스트
uv run python cli.py --help
uv run python cli.py list-datasets

# 웹 대시보드 테스트
uv run streamlit run src/presentation/web/main.py --server.headless true &
sleep 5
curl -s http://localhost:8501 > /dev/null && echo "✅ Dashboard OK" || echo "❌ Dashboard Failed"
pkill -f streamlit
```

#### 4.2 Docker 빌드 테스트
```bash
# 로컬 Docker 빌드 테스트
docker build -t ragtrace-clean .

# 빌드 성공 확인
docker images ragtrace-clean

# 컨테이너 실행 테스트
docker run --rm -d --name ragtrace-test -p 8502:8501 ragtrace-clean
sleep 10
curl -s http://localhost:8502 > /dev/null && echo "✅ Container OK" || echo "❌ Container Failed"
docker stop ragtrace-test
```

### 5단계: 문서 업데이트

#### 5.1 README.md 정리
```markdown
# 업데이트할 섹션들
1. 불필요한 개발 정보 제거
2. Docker 실행 방법을 맨 앞으로 이동
3. 간단한 설치 가이드 작성
4. 핵심 기능 중심으로 재구성
5. 문제 해결 섹션 간소화
```

#### 5.2 남은 문서들 검토
```bash
# 각 문서의 내용 검토 및 업데이트
# - Docker_Deployment_Guide.md: 최신 상태 유지
# - RAGTRACE_METRICS.md: 사용자 가이드로 유지  
# - Development_Guide.md: 간소화된 개발 가이드로 변경
```

### 6단계: 최종 커밋 및 태깅

#### 6.1 변경사항 커밋
```bash
# 모든 변경사항 확인
git status
git diff --name-status HEAD

# 커밋 생성
git add -A
git commit -m "feat: Clean up project for production release

- Remove development-specific files and directories
- Keep only essential files for production deployment
- Add .gitkeep files to maintain directory structure
- Update documentation for end-users
- Streamline project structure for easier maintenance

Removed:
- Development tools (justfile, uv-setup.sh, pytest.ini)
- Test coverage reports and temporary files
- Development process documentation
- Test data files and scripts

Maintained:
- Core application source code
- Docker deployment configuration
- Essential documentation
- Sample evaluation data
- Production-ready configuration files

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 6.2 프로덕션 태그 생성
```bash
# 프로덕션 릴리스 태그
git tag -a "v1.0.0" -m "First production release

Features:
- Multi-LLM RAG evaluation (Gemini, HCX, BGE-M3)
- Web dashboard with Streamlit
- CLI interface for batch processing  
- Docker deployment support
- Clean Architecture with dependency injection
- Comprehensive documentation

Ready for production deployment."

# 태그 푸시
git push origin cleanup/production-ready
git push origin v1.0.0
```

### 7단계: 브랜치 관리

#### 7.1 Pull Request 생성
```bash
# GitHub CLI 사용 (선택적)
gh pr create \
  --title "Production cleanup: Remove development files" \
  --body "$(cat <<EOF
## Summary
Clean up project structure for production release by removing development-specific files and keeping only essential components.

## Changes Made
- ✅ Removed development tools and scripts
- ✅ Removed test coverage reports and temporary files  
- ✅ Removed development process documentation
- ✅ Streamlined directory structure
- ✅ Updated documentation for end-users
- ✅ Maintained all core functionality

## Testing
- [x] Basic functionality tests passed
- [x] Docker build successful
- [x] Web dashboard working
- [x] CLI interface working

## File Changes
**Removed:**
- Development tools (justfile, uv-setup.sh, pytest.ini)
- Test coverage and temporary files
- Development documentation
- Test data files

**Maintained:**
- All source code (src/)
- Docker configuration
- Essential documentation
- Sample data
- Configuration files

This creates a clean, production-ready version suitable for end-users.

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)" \
  --base main \
  --head cleanup/production-ready
```

#### 7.2 메인 브랜치 병합 준비
```bash
# PR 검토 후 메인 브랜치로 병합
# (GitHub UI에서 수행 또는 CLI로)

# 병합 후 정리
git checkout main
git pull origin main
git branch -d cleanup/production-ready  # 로컬 브랜치 삭제
git push origin --delete cleanup/production-ready  # 원격 브랜치 삭제
```

## 검증 체크리스트

### 기능 검증
- [ ] CLI 명령어들이 정상 작동 (`--help`, `list-datasets`, `list-prompts`)
- [ ] 기본 평가 실행이 정상 작동
- [ ] 웹 대시보드가 정상 실행
- [ ] Docker 이미지 빌드 성공
- [ ] Docker 컨테이너 실행 성공

### 파일 구조 검증
- [ ] 모든 필수 파일이 존재
- [ ] 불필요한 개발 파일이 제거됨
- [ ] 디렉토리 구조가 유지됨
- [ ] .gitkeep 파일이 적절히 배치됨

### 문서 검증  
- [ ] README.md가 사용자 중심으로 업데이트됨
- [ ] Docker 배포 가이드가 최신 상태
- [ ] 메트릭 설명 문서가 유지됨
- [ ] 불필요한 개발 문서가 제거됨

### Git 관리 검증
- [ ] 백업 태그가 생성됨
- [ ] 정리 브랜치가 올바르게 생성됨
- [ ] 커밋 메시지가 명확함
- [ ] 프로덕션 태그가 적절함

## 예상 효과

### 프로젝트 크기 감소
- **개발 파일 제거**: ~50-100MB 감소 예상
- **테스트 파일 제거**: htmlcov, temp 등으로 추가 감소
- **불필요한 문서 제거**: 개발 과정 문서들 제거

### 사용자 경험 개선
- **단순한 프로젝트 구조**: 핵심 파일만 남아 이해하기 쉬움
- **명확한 문서**: 사용자 중심의 간결한 가이드
- **빠른 시작**: Docker 중심의 간편한 실행 방법

### 유지보수성 향상
- **핵심 코드 집중**: 프로덕션 관련 파일만 관리
- **명확한 의존성**: 필수 파일들만 남아 관리 용이
- **일관된 구조**: Clean Architecture 원칙 유지

## 주의사항

1. **백업 필수**: 작업 전 반드시 태그나 브랜치로 백업
2. **기능 테스트**: 각 단계에서 핵심 기능 동작 확인
3. **문서 업데이트**: README와 가이드 문서들 동기화
4. **Docker 검증**: 정리 후에도 Docker 빌드/실행 정상 확인
5. **브랜치 전략**: cleanup 브랜치에서 작업 후 PR로 검토

이 계획에 따라 단계별로 진행하면 안전하고 체계적으로 프로젝트를 정리할 수 있습니다.