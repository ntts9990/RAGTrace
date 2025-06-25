#!/usr/bin/env python3
"""
RAGTrace 엔터프라이즈 패키지 검증 및 진단 도구
설치 전후 시스템 상태 검증, 문제 진단, 성능 벤치마크
"""

import os
import sys
import json
import time
import platform
import subprocess
import importlib
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemInfo:
    """시스템 정보"""
    platform: str
    architecture: str
    python_version: str
    python_executable: str
    cpu_count: int
    memory_gb: float
    disk_free_gb: float
    
@dataclass
class ValidationResult:
    """검증 결과"""
    category: str
    check_name: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    details: str
    suggestion: Optional[str] = None
    performance_metric: Optional[float] = None

@dataclass
class DiagnosticReport:
    """진단 보고서"""
    timestamp: str
    system_info: SystemInfo
    validation_results: List[ValidationResult]
    overall_status: str
    recommendations: List[str]

class SystemAnalyzer:
    """시스템 분석기"""
    
    def __init__(self):
        self.system_info = self._collect_system_info()
    
    def _collect_system_info(self) -> SystemInfo:
        """시스템 정보 수집"""
        import psutil
        
        # 메모리 정보 (GB 단위)
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        # 디스크 정보 (GB 단위)
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        
        return SystemInfo(
            platform=platform.system(),
            architecture=platform.machine(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            python_executable=sys.executable,
            cpu_count=os.cpu_count() or 1,
            memory_gb=round(memory_gb, 2),
            disk_free_gb=round(disk_free_gb, 2)
        )
    
    def check_system_requirements(self) -> List[ValidationResult]:
        """시스템 요구사항 확인"""
        results = []
        
        # Python 버전 확인
        if sys.version_info >= (3, 11):
            results.append(ValidationResult(
                category="System",
                check_name="Python Version",
                status="PASS",
                details=f"Python {self.system_info.python_version}"
            ))
        else:
            results.append(ValidationResult(
                category="System",
                check_name="Python Version",
                status="FAIL",
                details=f"Python {self.system_info.python_version} (3.11+ required)",
                suggestion="Python 3.11 이상으로 업그레이드하세요"
            ))
        
        # 메모리 확인 (최소 4GB)
        if self.system_info.memory_gb >= 4.0:
            results.append(ValidationResult(
                category="System",
                check_name="Memory",
                status="PASS",
                details=f"{self.system_info.memory_gb}GB RAM"
            ))
        else:
            results.append(ValidationResult(
                category="System",
                check_name="Memory",
                status="WARN",
                details=f"{self.system_info.memory_gb}GB RAM (4GB+ recommended)",
                suggestion="더 많은 메모리가 권장됩니다"
            ))
        
        # 디스크 공간 확인 (최소 5GB)
        if self.system_info.disk_free_gb >= 5.0:
            results.append(ValidationResult(
                category="System",
                check_name="Disk Space",
                status="PASS",
                details=f"{self.system_info.disk_free_gb}GB free"
            ))
        else:
            results.append(ValidationResult(
                category="System",
                check_name="Disk Space",
                status="FAIL",
                details=f"{self.system_info.disk_free_gb}GB free (5GB+ required)",
                suggestion="디스크 공간을 확보하세요"
            ))
        
        return results

class PackageValidator:
    """패키지 검증기"""
    
    def __init__(self, package_path: Optional[Path] = None):
        self.package_path = package_path
        
    def validate_uv_installation(self) -> ValidationResult:
        """UV 설치 검증"""
        try:
            result = subprocess.run(["uv", "--version"], 
                                  capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            return ValidationResult(
                category="Tools",
                check_name="UV Package Manager",
                status="PASS",
                details=f"UV {version}"
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ValidationResult(
                category="Tools",
                check_name="UV Package Manager",
                status="FAIL",
                details="UV not installed",
                suggestion="UV를 설치하세요: curl -LsSf https://astral.sh/uv/install.sh | sh"
            )
    
    def validate_core_packages(self) -> List[ValidationResult]:
        """핵심 패키지 설치 검증"""
        results = []
        
        core_packages = {
            'streamlit': 'Streamlit 웹 프레임워크',
            'pandas': 'Pandas 데이터 처리',
            'numpy': 'NumPy 수치 계산',
            'torch': 'PyTorch 머신러닝',
            'sentence_transformers': 'Sentence Transformers',
            'ragas': 'RAGAS 평가 프레임워크',
            'dependency_injector': 'Dependency Injector',
            'google.generativeai': 'Google AI API',
            'plotly': 'Plotly 시각화',
            'openpyxl': 'Excel 파일 처리',
            'requests': 'HTTP 클라이언트'
        }
        
        for package_name, description in core_packages.items():
            try:
                start_time = time.time()
                
                # 모듈 import 테스트
                if '.' in package_name:
                    # 패키지.모듈 형태
                    parts = package_name.split('.')
                    module = importlib.import_module(parts[0])
                    for part in parts[1:]:
                        module = getattr(module, part)
                else:
                    module = importlib.import_module(package_name)
                
                import_time = time.time() - start_time
                version = getattr(module, '__version__', 'unknown')
                
                results.append(ValidationResult(
                    category="Packages",
                    check_name=description,
                    status="PASS",
                    details=f"v{version}",
                    performance_metric=import_time
                ))
                
            except ImportError as e:
                results.append(ValidationResult(
                    category="Packages",
                    check_name=description,
                    status="FAIL",
                    details=f"Import failed: {str(e)[:50]}...",
                    suggestion=f"패키지를 설치하세요: uv pip install {package_name.split('.')[0]}"
                ))
            except Exception as e:
                results.append(ValidationResult(
                    category="Packages",
                    check_name=description,
                    status="WARN",
                    details=f"Validation error: {str(e)[:50]}...",
                    suggestion="패키지 설치 상태를 확인하세요"
                ))
        
        return results
    
    def validate_ragtrace_functionality(self) -> List[ValidationResult]:
        """RAGTrace 기능 검증"""
        results = []
        
        # CLI 모듈 import 테스트
        try:
            sys.path.insert(0, str(Path.cwd()))
            import cli
            
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="CLI Module",
                status="PASS",
                details="CLI 모듈 import 성공"
            ))
        except ImportError as e:
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="CLI Module",
                status="FAIL",
                details=f"CLI import failed: {e}",
                suggestion="RAGTrace 소스 디렉토리에서 실행하세요"
            ))
        
        # 컨테이너 모듈 테스트
        try:
            from src.container import container
            
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="DI Container",
                status="PASS",
                details="의존성 주입 컨테이너 로드 성공"
            ))
        except ImportError as e:
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="DI Container",
                status="FAIL",
                details=f"Container import failed: {e}",
                suggestion="src/ 디렉토리와 의존성을 확인하세요"
            ))
        
        # 환경 설정 파일 확인
        env_files = [".env", ".env.example"]
        env_exists = any(Path(f).exists() for f in env_files)
        
        if env_exists:
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="Environment Config",
                status="PASS",
                details="환경 설정 파일 존재"
            ))
        else:
            results.append(ValidationResult(
                category="RAGTrace",
                check_name="Environment Config",
                status="WARN",
                details="환경 설정 파일 없음",
                suggestion=".env.example을 .env로 복사하고 API 키를 설정하세요"
            ))
        
        return results

class PerformanceBenchmark:
    """성능 벤치마크"""
    
    def __init__(self):
        self.results = []
    
    def run_import_benchmark(self) -> List[ValidationResult]:
        """패키지 import 성능 벤치마크"""
        results = []
        
        heavy_packages = ['torch', 'transformers', 'sentence_transformers', 'streamlit']
        
        for package in heavy_packages:
            try:
                start_time = time.time()
                importlib.import_module(package)
                import_time = time.time() - start_time
                
                # 성능 기준: 10초 이내
                status = "PASS" if import_time < 10.0 else "WARN"
                
                results.append(ValidationResult(
                    category="Performance",
                    check_name=f"{package} Import Speed",
                    status=status,
                    details=f"{import_time:.2f}초",
                    performance_metric=import_time,
                    suggestion="느린 import가 감지되었습니다" if status == "WARN" else None
                ))
                
            except ImportError:
                results.append(ValidationResult(
                    category="Performance",
                    check_name=f"{package} Import Speed",
                    status="SKIP",
                    details="패키지가 설치되지 않음"
                ))
        
        return results
    
    def run_cpu_benchmark(self) -> ValidationResult:
        """CPU 성능 벤치마크"""
        try:
            import numpy as np
            
            # 간단한 행렬 연산 벤치마크
            size = 1000
            start_time = time.time()
            
            a = np.random.rand(size, size)
            b = np.random.rand(size, size)
            c = np.dot(a, b)
            
            cpu_time = time.time() - start_time
            
            # 성능 기준: 5초 이내
            status = "PASS" if cpu_time < 5.0 else "WARN"
            
            return ValidationResult(
                category="Performance",
                check_name="CPU Benchmark",
                status=status,
                details=f"Matrix multiplication ({size}x{size}): {cpu_time:.2f}초",
                performance_metric=cpu_time,
                suggestion="CPU 성능이 낮습니다" if status == "WARN" else None
            )
            
        except Exception as e:
            return ValidationResult(
                category="Performance",
                check_name="CPU Benchmark",
                status="FAIL",
                details=f"벤치마크 실패: {e}",
                suggestion="NumPy를 설치하세요"
            )
    
    def run_memory_benchmark(self) -> ValidationResult:
        """메모리 사용량 벤치마크"""
        try:
            import psutil
            import gc
            
            # 메모리 사용량 측정
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024**2)  # MB
            
            # 메모리 집약적 작업 시뮬레이션
            import pandas as pd
            df = pd.DataFrame({'data': range(100000)})
            df_processed = df.groupby(df.index // 1000).sum()
            
            peak_memory = process.memory_info().rss / (1024**2)  # MB
            memory_usage = peak_memory - initial_memory
            
            # 정리
            del df, df_processed
            gc.collect()
            
            # 성능 기준: 500MB 이내
            status = "PASS" if memory_usage < 500 else "WARN"
            
            return ValidationResult(
                category="Performance",
                check_name="Memory Usage",
                status=status,
                details=f"Peak usage: {memory_usage:.1f}MB",
                performance_metric=memory_usage,
                suggestion="메모리 사용량이 높습니다" if status == "WARN" else None
            )
            
        except Exception as e:
            return ValidationResult(
                category="Performance",
                check_name="Memory Usage",
                status="FAIL",
                details=f"벤치마크 실패: {e}",
                suggestion="psutil을 설치하세요"
            )

class SecurityChecker:
    """보안 검사"""
    
    def __init__(self):
        pass
    
    def check_package_vulnerabilities(self) -> ValidationResult:
        """패키지 취약점 검사"""
        try:
            # Safety를 사용한 취약점 검사
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                # JSON 출력 파싱
                output = result.stdout.strip()
                if output:
                    vulnerabilities = json.loads(output)
                    vuln_count = len(vulnerabilities)
                    
                    if vuln_count == 0:
                        return ValidationResult(
                            category="Security",
                            check_name="Package Vulnerabilities",
                            status="PASS",
                            details="취약점 없음"
                        )
                    else:
                        return ValidationResult(
                            category="Security",
                            check_name="Package Vulnerabilities",
                            status="WARN",
                            details=f"{vuln_count}개 취약점 발견",
                            suggestion="취약점이 있는 패키지를 업데이트하세요"
                        )
                else:
                    return ValidationResult(
                        category="Security",
                        check_name="Package Vulnerabilities",
                        status="PASS",
                        details="취약점 없음"
                    )
            else:
                return ValidationResult(
                    category="Security",
                    check_name="Package Vulnerabilities",
                    status="FAIL",
                    details="보안 검사 실행 실패",
                    suggestion="safety 도구를 설치하세요: pip install safety"
                )
                
        except subprocess.TimeoutExpired:
            return ValidationResult(
                category="Security",
                check_name="Package Vulnerabilities",
                status="WARN",
                details="보안 검사 시간 초과",
                suggestion="네트워크 연결을 확인하세요"
            )
        except FileNotFoundError:
            return ValidationResult(
                category="Security",
                check_name="Package Vulnerabilities",
                status="SKIP",
                details="Safety 도구 미설치",
                suggestion="pip install safety 로 설치하세요"
            )
        except Exception as e:
            return ValidationResult(
                category="Security",
                check_name="Package Vulnerabilities",
                status="FAIL",
                details=f"검사 실패: {e}",
                suggestion="보안 검사 도구를 확인하세요"
            )
    
    def check_environment_security(self) -> List[ValidationResult]:
        """환경 보안 검사"""
        results = []
        
        # .env 파일 권한 확인
        env_file = Path(".env")
        if env_file.exists():
            # Unix/Linux에서 파일 권한 확인
            if hasattr(os, 'stat'):
                import stat
                file_stat = env_file.stat()
                file_mode = stat.filemode(file_stat.st_mode)
                
                # 다른 사용자가 읽을 수 있는지 확인
                if file_stat.st_mode & stat.S_IROTH:
                    results.append(ValidationResult(
                        category="Security",
                        check_name="Environment File Permissions",
                        status="WARN",
                        details=f".env 파일 권한: {file_mode}",
                        suggestion="chmod 600 .env 로 권한을 제한하세요"
                    ))
                else:
                    results.append(ValidationResult(
                        category="Security",
                        check_name="Environment File Permissions",
                        status="PASS",
                        details=f".env 파일 권한: {file_mode}"
                    ))
        
        # API 키 설정 확인 (실제 값은 확인하지 않음)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_keys = ['GEMINI_API_KEY', 'CLOVA_STUDIO_API_KEY']
            configured_keys = []
            
            for key in api_keys:
                if os.getenv(key):
                    configured_keys.append(key)
            
            if configured_keys:
                results.append(ValidationResult(
                    category="Security",
                    check_name="API Key Configuration",
                    status="PASS",
                    details=f"{len(configured_keys)}개 API 키 설정됨"
                ))
            else:
                results.append(ValidationResult(
                    category="Security",
                    check_name="API Key Configuration",
                    status="WARN",
                    details="API 키가 설정되지 않음",
                    suggestion=".env 파일에 API 키를 설정하세요"
                ))
                
        except ImportError:
            results.append(ValidationResult(
                category="Security",
                check_name="API Key Configuration",
                status="SKIP",
                details="python-dotenv가 설치되지 않음"
            ))
        
        return results

class EnterpriseValidator:
    """엔터프라이즈 검증기 메인 클래스"""
    
    def __init__(self, package_path: Optional[Path] = None):
        self.package_path = package_path
        self.system_analyzer = SystemAnalyzer()
        self.package_validator = PackageValidator(package_path)
        self.performance_benchmark = PerformanceBenchmark()
        self.security_checker = SecurityChecker()
        
    def run_complete_validation(self) -> DiagnosticReport:
        """완전한 검증 실행"""
        logger.info("🔍 RAGTrace 엔터프라이즈 검증 시작")
        
        all_results = []
        
        # 1. 시스템 요구사항 검증
        logger.info("1️⃣ 시스템 요구사항 검증 중...")
        all_results.extend(self.system_analyzer.check_system_requirements())
        
        # 2. 도구 및 패키지 검증
        logger.info("2️⃣ 도구 및 패키지 검증 중...")
        all_results.append(self.package_validator.validate_uv_installation())
        all_results.extend(self.package_validator.validate_core_packages())
        
        # 3. RAGTrace 기능 검증
        logger.info("3️⃣ RAGTrace 기능 검증 중...")
        all_results.extend(self.package_validator.validate_ragtrace_functionality())
        
        # 4. 성능 벤치마크
        logger.info("4️⃣ 성능 벤치마크 실행 중...")
        all_results.extend(self.performance_benchmark.run_import_benchmark())
        all_results.append(self.performance_benchmark.run_cpu_benchmark())
        all_results.append(self.performance_benchmark.run_memory_benchmark())
        
        # 5. 보안 검사
        logger.info("5️⃣ 보안 검사 실행 중...")
        all_results.append(self.security_checker.check_package_vulnerabilities())
        all_results.extend(self.security_checker.check_environment_security())
        
        # 결과 분석
        overall_status, recommendations = self._analyze_results(all_results)
        
        # 진단 보고서 생성
        report = DiagnosticReport(
            timestamp=datetime.now().isoformat(),
            system_info=self.system_analyzer.system_info,
            validation_results=all_results,
            overall_status=overall_status,
            recommendations=recommendations
        )
        
        logger.info(f"✅ 검증 완료: {overall_status}")
        return report
    
    def _analyze_results(self, results: List[ValidationResult]) -> Tuple[str, List[str]]:
        """결과 분석 및 권장사항 생성"""
        fail_count = sum(1 for r in results if r.status == "FAIL")
        warn_count = sum(1 for r in results if r.status == "WARN")
        pass_count = sum(1 for r in results if r.status == "PASS")
        
        if fail_count > 0:
            overall_status = "CRITICAL"
        elif warn_count > pass_count:
            overall_status = "WARNING"
        elif warn_count > 0:
            overall_status = "GOOD"
        else:
            overall_status = "EXCELLENT"
        
        # 권장사항 수집
        recommendations = []
        for result in results:
            if result.suggestion and result.status in ["FAIL", "WARN"]:
                recommendations.append(f"{result.check_name}: {result.suggestion}")
        
        return overall_status, recommendations
    
    def print_report(self, report: DiagnosticReport) -> None:
        """진단 보고서 출력"""
        print("\n" + "="*80)
        print("🏥 RAGTrace 엔터프라이즈 진단 보고서")
        print("="*80)
        
        # 시스템 정보
        print(f"\n📊 시스템 정보:")
        print(f"   플랫폼: {report.system_info.platform} {report.system_info.architecture}")
        print(f"   Python: {report.system_info.python_version}")
        print(f"   CPU: {report.system_info.cpu_count} cores")
        print(f"   메모리: {report.system_info.memory_gb}GB")
        print(f"   디스크: {report.system_info.disk_free_gb}GB 여유")
        
        # 전체 상태
        status_colors = {
            "EXCELLENT": "🟢",
            "GOOD": "🟡", 
            "WARNING": "🟠",
            "CRITICAL": "🔴"
        }
        print(f"\n🎯 전체 상태: {status_colors.get(report.overall_status, '❓')} {report.overall_status}")
        
        # 카테고리별 결과
        categories = {}
        for result in report.validation_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            print(f"\n📋 {category}:")
            for result in results:
                status_icon = {
                    "PASS": "✅",
                    "WARN": "⚠️", 
                    "FAIL": "❌",
                    "SKIP": "⏭️"
                }.get(result.status, "❓")
                
                print(f"   {status_icon} {result.check_name}: {result.details}")
                
                if result.performance_metric:
                    print(f"      ⏱️ 성능: {result.performance_metric:.3f}")
                
                if result.suggestion:
                    print(f"      💡 제안: {result.suggestion}")
        
        # 권장사항
        if report.recommendations:
            print(f"\n🔧 권장사항:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
    
    def save_report(self, report: DiagnosticReport, output_file: Path) -> None:
        """진단 보고서 저장"""
        report_data = asdict(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"진단 보고서 저장: {output_file}")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAGTrace 엔터프라이즈 검증 및 진단")
    parser.add_argument("--package-path", type=Path,
                      help="패키지 경로 (선택사항)")
    parser.add_argument("--output", type=Path, default="diagnostic_report.json",
                      help="진단 보고서 출력 파일")
    parser.add_argument("--quiet", action="store_true",
                      help="간략한 출력")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # 검증 실행
    validator = EnterpriseValidator(args.package_path)
    report = validator.run_complete_validation()
    
    # 보고서 출력
    if not args.quiet:
        validator.print_report(report)
    
    # 보고서 저장
    validator.save_report(report, args.output)
    
    # 종료 코드 설정
    if report.overall_status in ["CRITICAL"]:
        sys.exit(1)
    elif report.overall_status in ["WARNING"]:
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()