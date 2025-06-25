# 📚 RAGTrace 문서 센터

RAGTrace 사용을 위한 종합 문서 모음입니다. 목적에 따라 적절한 가이드를 선택하세요.

## 🚀 빠른 시작

| 목적 | 문서 | 설명 |
|------|------|------|
| **설치하기** | [📦 INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | 모든 환경의 설치 방법 |
| **Windows 설치** | [🪟 WINDOWS_SETUP.md](WINDOWS_SETUP.md) | Windows 특화 상세 가이드 |
| **평가 이해하기** | [📊 RAGTRACE_METRICS.md](RAGTRACE_METRICS.md) | 평가 지표 완전 가이드 |
| **문제 해결** | [🚨 TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 문제 해결 및 진단 |

## 📖 상세 가이드

### 설치 및 환경 설정
- **[설치 가이드](INSTALLATION_GUIDE.md)** - UV, Docker, 오프라인 설치
- **[Windows 설치](WINDOWS_SETUP.md)** - Windows 환경 완전 가이드
- **[문제 해결](TROUBLESHOOTING.md)** - 일반적인 설치/실행 문제

### 사용법 및 활용
- **[데이터 가져오기](Data_Import_Guide.md)** - Excel/CSV 데이터 처리
- **[메트릭 이해](RAGTRACE_METRICS.md)** - 5가지 RAGAS 메트릭 완전 분석
- **[Docker 배포](Docker_Deployment_Guide.md)** - 컨테이너 기반 배포

### 개발 및 확장
- **[아키텍처 가이드](ARCHITECTURE_AND_DEVELOPMENT.md)** - 시스템 구조 및 개발 가이드

## 🎯 사용자별 추천 경로

### 🔰 처음 사용하는 경우
1. **[설치 가이드](INSTALLATION_GUIDE.md)** - 환경에 맞는 설치 방법 선택
2. **[메트릭 가이드](RAGTRACE_METRICS.md)** - 평가 지표 이해
3. **[데이터 가이드](Data_Import_Guide.md)** - 데이터 준비 방법

### 🪟 Windows 사용자
1. **[Windows 설치](WINDOWS_SETUP.md)** - Windows 특화 설치 가이드
2. **[문제 해결](TROUBLESHOOTING.md)** - Windows 관련 문제 해결

### 🏢 엔터프라이즈 환경
1. **[설치 가이드](INSTALLATION_GUIDE.md#-오프라인-설치-엔터프라이즈)** - 폐쇄망 설치
2. **[Docker 가이드](Docker_Deployment_Guide.md)** - 컨테이너 배포
3. **[아키텍처 가이드](ARCHITECTURE_AND_DEVELOPMENT.md)** - 시스템 확장

### 👨‍💻 개발자
1. **[아키텍처 가이드](ARCHITECTURE_AND_DEVELOPMENT.md)** - 코드 구조 이해
2. **[설치 가이드](INSTALLATION_GUIDE.md#⚡-uv-설치-권장)** - 개발 환경 설정

## 📋 문서 구조

```
docs/
├── README.md                           # 📚 이 파일 (문서 센터)
├── INSTALLATION_GUIDE.md               # 📦 통합 설치 가이드
├── WINDOWS_SETUP.md                    # 🪟 Windows 특화 가이드
├── RAGTRACE_METRICS.md                 # 📊 메트릭 완전 분석
├── TROUBLESHOOTING.md                  # 🚨 문제 해결
├── Data_Import_Guide.md                # 📄 데이터 가져오기
├── Docker_Deployment_Guide.md          # 🐳 Docker 배포
├── ARCHITECTURE_AND_DEVELOPMENT.md     # 🏗️ 아키텍처 & 개발
└── archive/                            # 📁 이전 버전 문서들
    ├── Windows_설치_가이드.md           
    ├── SETUP-WINDOWS.md
    ├── UV_SETUP.md
    └── ...
```

## 🎨 문서 표기법

문서에서 사용하는 표기법과 아이콘 의미:

| 표기 | 의미 |
|------|------|
| 🎯 | 중요한 목표나 핵심 포인트 |
| ⚡ | 빠른 방법이나 권장 사항 |
| 🚨 | 주의사항이나 문제 상황 |
| 💡 | 팁이나 추가 정보 |
| ✅ | 성공 상태나 완료 |
| ❌ | 실패 상태나 문제 |
| 🔧 | 설정이나 구성 |
| 📦 | 패키지나 설치 관련 |

## 🔄 업데이트 정보

### 최신 업데이트 (v2.1)
- **Windows 자동 설치**: Python부터 완전 자동화
- **PowerShell 호환성**: 5.1+ 완전 지원
- **오프라인 패키지**: 엔터프라이즈급 폐쇄망 지원
- **Answer Correctness**: 5번째 RAGAS 메트릭 완전 통합

### 문서 변경사항
- 통합 설치 가이드로 모든 플랫폼 지원
- Windows 전용 상세 가이드 추가
- 최신 UV 패키지 매니저 반영
- 폐쇄망 설치 프로세스 완전 문서화

## 📞 지원 및 문의

### 일반 지원
- **GitHub Issues**: https://github.com/ntts9990/RAGTrace/issues
- **프로젝트 홈**: https://github.com/ntts9990/RAGTrace

### 문서 개선 제안
문서 개선이나 추가 요청이 있으시면:
1. GitHub Issues에 `documentation` 라벨로 등록
2. 구체적인 개선 사항이나 누락된 내용 명시
3. 어떤 상황에서 필요한지 컨텍스트 제공

## 🎯 다음 단계

문서를 확인했다면:

1. **환경에 맞는 설치 진행** - [설치 가이드](INSTALLATION_GUIDE.md) 참조
2. **첫 번째 평가 실행** - 샘플 데이터로 테스트
3. **실제 데이터 준비** - [데이터 가이드](Data_Import_Guide.md) 참조
4. **결과 분석 및 활용** - [메트릭 가이드](RAGTRACE_METRICS.md) 참조

RAGTrace로 효과적인 RAG 시스템 평가를 시작하세요! 🚀