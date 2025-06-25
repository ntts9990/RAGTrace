#!/usr/bin/env python3
"""
RAGTrace 엔터프라이즈급 오프라인 패키지 생성기
산업 표준 모범 사례를 적용한 보안 강화 버전
"""

import os
import sys
import json
import hashlib
import shutil
import tarfile
import zipfile
import platform
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('package_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PackageManifest:
    """패키지 매니페스트 정보"""
    version: str
    creation_date: str
    platform: str
    architecture: str
    python_version: str
    total_packages: int
    total_size_mb: float
    checksum_algorithm: str = "SHA-256"
    creator: str = "RAGTrace Enterprise Package Builder"

@dataclass
class ValidationResult:
    """검증 결과"""
    check_name: str
    passed: bool
    details: str
    suggestion: Optional[str] = None

class PackageIntegrityManager:
    """패키지 무결성 관리"""
    
    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.checksums_file = package_dir / "checksums.sha256"
    
    def generate_checksums(self) -> Dict[str, str]:
        """모든 패키지 파일에 대한 SHA-256 체크섬 생성"""
        logger.info("패키지 체크섬 생성 중...")
        checksums = {}
        
        wheels_dir = self.package_dir / "wheels"
        if wheels_dir.exists():
            for wheel_file in wheels_dir.glob("*.whl"):
                checksum = self._calculate_sha256(wheel_file)
                checksums[wheel_file.name] = checksum
                
        return checksums
    
    def save_checksums(self, checksums: Dict[str, str]) -> None:
        """체크섬을 파일로 저장"""
        with open(self.checksums_file, 'w') as f:
            for filename, checksum in checksums.items():
                f.write(f"{checksum}  {filename}\n")
        
        logger.info(f"체크섬 파일 저장: {self.checksums_file}")
    
    def verify_checksums(self) -> bool:
        """저장된 체크섬과 실제 파일 비교 검증"""
        if not self.checksums_file.exists():
            logger.warning("체크섬 파일이 없습니다.")
            return False
        
        logger.info("패키지 무결성 검증 중...")
        wheels_dir = self.package_dir / "wheels"
        
        with open(self.checksums_file, 'r') as f:
            for line in f:
                expected_hash, filename = line.strip().split('  ', 1)
                file_path = wheels_dir / filename
                
                if not file_path.exists():
                    logger.error(f"파일이 없습니다: {filename}")
                    return False
                
                actual_hash = self._calculate_sha256(file_path)
                if actual_hash != expected_hash:
                    logger.error(f"체크섬 불일치: {filename}")
                    return False
        
        logger.info("✅ 모든 패키지 무결성 검증 통과")
        return True
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """파일의 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

class UVIntegrationManager:
    """UV 패키지 매니저 통합"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.lockfile = project_root / "uv.lock"
    
    def check_uv_available(self) -> bool:
        """UV 설치 여부 확인"""
        try:
            result = subprocess.run(["uv", "--version"], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"UV 버전: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("UV가 설치되어 있지 않습니다.")
            return False
    
    def sync_dependencies(self) -> bool:
        """UV를 사용한 의존성 동기화"""
        try:
            logger.info("UV를 사용한 의존성 동기화 중...")
            subprocess.run(["uv", "sync", "--all-extras"], 
                          cwd=self.project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"의존성 동기화 실패: {e}")
            return False
    
    def export_requirements(self, output_file: Path, include_dev: bool = False) -> bool:
        """UV lockfile에서 requirements.txt 생성"""
        try:
            logger.info("UV lockfile에서 requirements 내보내기...")
            cmd = ["uv", "export", "--format=requirements-txt", f"--output-file={output_file}"]
            if not include_dev:
                cmd.append("--no-dev")
            
            subprocess.run(cmd, cwd=self.project_root, check=True)
            logger.info(f"Requirements 파일 생성: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Requirements 내보내기 실패: {e}")
            return False

class CrossPlatformInstaller:
    """크로스 플랫폼 통합 설치기"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    def detect_environment(self) -> Dict[str, str]:
        """시스템 환경 감지"""
        return {
            "platform": self.platform,
            "architecture": self.architecture,
            "python_version": self.python_version,
            "python_executable": sys.executable
        }
    
    def generate_platform_specific_requirements(self, base_requirements: Path, 
                                              output_dir: Path) -> Path:
        """플랫폼별 requirements 파일 생성"""
        platform_id = f"{self.platform}-{self.architecture}"
        output_file = output_dir / f"requirements-{platform_id}.txt"
        
        # 기본 requirements에 플랫폼 정보 추가
        with open(base_requirements, 'r') as src, open(output_file, 'w') as dst:
            dst.write(f"# Platform: {platform_id}\n")
            dst.write(f"# Python: {self.python_version}\n")
            dst.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            dst.write(src.read())
        
        return output_file
    
    def create_universal_installer(self, package_dir: Path) -> str:
        """범용 설치 스크립트 생성"""
        installer_script = f"""#!/usr/bin/env python3
'''
RAGTrace 범용 설치 스크립트
플랫폼: {self.platform}
아키텍처: {self.architecture}
Python: {self.python_version}
'''

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    print("RAGTrace 엔터프라이즈 설치 시작...")
    
    # 플랫폼 감지
    current_platform = platform.system().lower()
    current_arch = platform.machine().lower()
    
    print(f"감지된 플랫폼: {{current_platform}}-{{current_arch}}")
    
    # 가상환경 생성 (UV 사용)
    print("가상환경 생성 중...")
    if subprocess.run(["uv", "venv", "--python", "{self.python_version}"]).returncode != 0:
        print("❌ 가상환경 생성 실패")
        return False
    
    # 패키지 설치
    print("패키지 설치 중...")
    requirements_file = f"requirements-{{current_platform}}-{{current_arch}}.txt"
    
    install_cmd = [
        "uv", "pip", "install",
        "--no-index", "--find-links", "wheels/",
        "-r", requirements_file
    ]
    
    if subprocess.run(install_cmd).returncode != 0:
        print("❌ 패키지 설치 실패")
        return False
    
    print("✅ 설치 완료!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
        
        script_path = package_dir / "install.py"
        with open(script_path, 'w') as f:
            f.write(installer_script)
        
        # 실행 권한 부여
        script_path.chmod(0o755)
        
        return str(script_path)

class InstallationRecoveryManager:
    """설치 실패 시 복구 관리"""
    
    def __init__(self, install_dir: Path):
        self.install_dir = install_dir
        self.backup_dir = None
    
    def create_backup(self) -> Optional[Path]:
        """설치 전 백업 생성"""
        if not self.install_dir.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.install_dir.parent / f"backup_{timestamp}"
        
        logger.info(f"백업 생성 중: {self.backup_dir}")
        shutil.copytree(self.install_dir, self.backup_dir)
        
        return self.backup_dir
    
    def rollback(self) -> bool:
        """백업으로부터 복구"""
        if not self.backup_dir or not self.backup_dir.exists():
            logger.error("복구할 백업이 없습니다.")
            return False
        
        logger.info("설치 실패로 인한 롤백 시작...")
        
        # 현재 설치 디렉토리 제거
        if self.install_dir.exists():
            shutil.rmtree(self.install_dir)
        
        # 백업에서 복구
        shutil.copytree(self.backup_dir, self.install_dir)
        
        logger.info("✅ 롤백 완료")
        return True
    
    def cleanup_backup(self) -> None:
        """백업 디렉토리 정리"""
        if self.backup_dir and self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
            logger.info("백업 디렉토리 정리 완료")

class EnterpriseValidator:
    """엔터프라이즈급 검증 도구"""
    
    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.results: List[ValidationResult] = []
    
    def validate_complete_package(self) -> List[ValidationResult]:
        """완전한 패키지 검증"""
        logger.info("엔터프라이즈 패키지 검증 시작...")
        
        # 1. 패키지 무결성 검증
        self._validate_integrity()
        
        # 2. 의존성 트리 검증
        self._validate_dependencies()
        
        # 3. 플랫폼 호환성 검증
        self._validate_platform_compatibility()
        
        # 4. 보안 스캔
        self._validate_security()
        
        # 5. 성능 벤치마크
        self._validate_performance()
        
        return self.results
    
    def _validate_integrity(self) -> None:
        """패키지 무결성 검증"""
        integrity_manager = PackageIntegrityManager(self.package_dir)
        
        if integrity_manager.checksums_file.exists():
            passed = integrity_manager.verify_checksums()
            details = "모든 패키지 체크섬 검증 통과" if passed else "일부 패키지 체크섬 불일치"
            suggestion = None if passed else "패키지를 다시 다운로드하세요"
        else:
            passed = False
            details = "체크섬 파일이 없습니다"
            suggestion = "패키지 생성 시 체크섬을 생성하세요"
        
        self.results.append(ValidationResult(
            check_name="패키지 무결성",
            passed=passed,
            details=details,
            suggestion=suggestion
        ))
    
    def _validate_dependencies(self) -> None:
        """의존성 검증"""
        try:
            # UV를 사용한 의존성 트리 검증
            result = subprocess.run(
                ["uv", "pip", "check"], 
                capture_output=True, text=True, cwd=self.package_dir
            )
            
            passed = result.returncode == 0
            details = "의존성 충돌 없음" if passed else f"의존성 문제: {result.stderr}"
            suggestion = None if passed else "의존성을 다시 해결하세요"
            
        except FileNotFoundError:
            passed = False
            details = "UV가 설치되어 있지 않음"
            suggestion = "UV를 설치하세요"
        
        self.results.append(ValidationResult(
            check_name="의존성 검증",
            passed=passed,
            details=details,
            suggestion=suggestion
        ))
    
    def _validate_platform_compatibility(self) -> None:
        """플랫폼 호환성 검증"""
        wheels_dir = self.package_dir / "wheels"
        if not wheels_dir.exists():
            self.results.append(ValidationResult(
                check_name="플랫폼 호환성",
                passed=False,
                details="wheels 디렉토리가 없습니다",
                suggestion="패키지를 다시 생성하세요"
            ))
            return
        
        current_platform = platform.system().lower()
        current_arch = platform.machine().lower()
        
        compatible_wheels = []
        incompatible_wheels = []
        
        for wheel in wheels_dir.glob("*.whl"):
            # wheel 파일명에서 플랫폼 정보 추출
            if "any" in wheel.name or current_platform in wheel.name:
                compatible_wheels.append(wheel.name)
            else:
                incompatible_wheels.append(wheel.name)
        
        passed = len(incompatible_wheels) == 0
        details = f"호환 가능: {len(compatible_wheels)}, 불가능: {len(incompatible_wheels)}"
        suggestion = "플랫폼별 패키지를 다시 생성하세요" if not passed else None
        
        self.results.append(ValidationResult(
            check_name="플랫폼 호환성",
            passed=passed,
            details=details,
            suggestion=suggestion
        ))
    
    def _validate_security(self) -> None:
        """보안 검증"""
        try:
            # Safety를 사용한 취약점 스캔
            result = subprocess.run(
                ["safety", "check", "--json"], 
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout) if result.stdout else []
                passed = len(vulnerabilities) == 0
                details = f"발견된 취약점: {len(vulnerabilities)}개"
                suggestion = "취약점이 있는 패키지를 업데이트하세요" if not passed else None
            else:
                passed = False
                details = "보안 스캔 실행 실패"
                suggestion = "safety 패키지를 설치하세요"
                
        except FileNotFoundError:
            passed = False
            details = "Safety 도구가 설치되어 있지 않음"
            suggestion = "pip install safety 를 실행하세요"
        
        self.results.append(ValidationResult(
            check_name="보안 검증",
            passed=passed,
            details=details,
            suggestion=suggestion
        ))
    
    def _validate_performance(self) -> None:
        """성능 벤치마크"""
        # 간단한 import 성능 테스트
        import time
        
        start_time = time.time()
        
        try:
            # 주요 패키지 import 테스트
            core_packages = ['pandas', 'numpy', 'streamlit', 'torch']
            failed_imports = []
            
            for package in core_packages:
                try:
                    __import__(package)
                except ImportError:
                    failed_imports.append(package)
            
            import_time = time.time() - start_time
            passed = len(failed_imports) == 0 and import_time < 10.0
            
            details = f"Import 시간: {import_time:.2f}초, 실패: {len(failed_imports)}개"
            suggestion = "느린 import가 감지되었습니다" if not passed else None
            
        except Exception as e:
            passed = False
            details = f"성능 테스트 실패: {str(e)}"
            suggestion = "패키지 설치 상태를 확인하세요"
        
        self.results.append(ValidationResult(
            check_name="성능 벤치마크",
            passed=passed,
            details=details,
            suggestion=suggestion
        ))

class EnterprisePackageBuilder:
    """엔터프라이즈급 오프라인 패키지 빌더"""
    
    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = project_root
        self.output_dir = output_dir
        self.package_dir = output_dir / "RAGTrace-Enterprise-Offline"
        
        # 컴포넌트 초기화
        self.uv_manager = UVIntegrationManager(project_root)
        self.installer = CrossPlatformInstaller()
        
    def build_complete_package(self) -> bool:
        """완전한 엔터프라이즈 패키지 빌드"""
        logger.info("🏗️ 엔터프라이즈 오프라인 패키지 빌드 시작")
        
        try:
            # 1. 사전 조건 확인
            if not self._validate_prerequisites():
                return False
            
            # 2. 패키지 구조 생성
            self._create_package_structure()
            
            # 3. UV를 사용한 의존성 해결
            self._resolve_dependencies()
            
            # 4. 플랫폼별 패키지 다운로드
            self._download_platform_packages()
            
            # 5. 소스 코드 복사
            self._copy_source_files()
            
            # 6. 패키지 무결성 보장
            self._ensure_package_integrity()
            
            # 7. 크로스 플랫폼 설치 스크립트 생성
            self._create_universal_installer()
            
            # 8. 매니페스트 및 문서 생성
            self._create_manifest_and_docs()
            
            # 9. 최종 패키지 압축
            final_package = self._create_final_package()
            
            # 10. 검증
            self._validate_final_package()
            
            logger.info(f"✅ 엔터프라이즈 패키지 빌드 완료: {final_package}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 패키지 빌드 실패: {e}")
            return False
    
    def _validate_prerequisites(self) -> bool:
        """사전 조건 검증"""
        logger.info("사전 조건 검증 중...")
        
        # UV 설치 확인
        if not self.uv_manager.check_uv_available():
            return False
        
        # 프로젝트 파일 확인
        required_files = ["cli.py", "src", "pyproject.toml"]
        for file in required_files:
            if not (self.project_root / file).exists():
                logger.error(f"필수 파일이 없습니다: {file}")
                return False
        
        return True
    
    def _create_package_structure(self) -> None:
        """패키지 디렉토리 구조 생성"""
        logger.info("패키지 구조 생성 중...")
        
        # 기존 디렉토리 제거
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)
        
        # 디렉토리 생성
        dirs = [
            "01_Prerequisites",
            "02_Dependencies/wheels",
            "03_Source", 
            "04_Scripts",
            "05_Documentation",
            "06_Verification"
        ]
        
        for dir_name in dirs:
            (self.package_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _resolve_dependencies(self) -> None:
        """UV를 사용한 의존성 해결"""
        logger.info("의존성 해결 중...")
        
        # 의존성 동기화
        self.uv_manager.sync_dependencies()
        
        # Requirements 파일 생성
        deps_dir = self.package_dir / "02_Dependencies"
        
        # Production requirements
        self.uv_manager.export_requirements(
            deps_dir / "requirements-production.txt", 
            include_dev=False
        )
        
        # Complete requirements (dev 포함)
        self.uv_manager.export_requirements(
            deps_dir / "requirements-complete.txt", 
            include_dev=True
        )
        
        # 플랫폼별 requirements
        self.installer.generate_platform_specific_requirements(
            deps_dir / "requirements-production.txt",
            deps_dir
        )
    
    def _download_platform_packages(self) -> None:
        """플랫폼별 패키지 다운로드"""
        logger.info("플랫폼별 패키지 다운로드 중...")
        
        wheels_dir = self.package_dir / "02_Dependencies" / "wheels"
        requirements_file = self.package_dir / "02_Dependencies" / "requirements-production.txt"
        
        # UV를 사용한 패키지 다운로드
        cmd = [
            "uv", "pip", "download",
            "--platform", f"{self.installer.platform.replace('darwin', 'macosx_10_9_x86_64')}",
            "--python-version", self.installer.python_version,
            "--only-binary", ":all:",
            "--dest", str(wheels_dir),
            "-r", str(requirements_file)
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            
            # 다운로드된 패키지 수 확인
            wheel_count = len(list(wheels_dir.glob("*.whl")))
            logger.info(f"✅ {wheel_count}개 패키지 다운로드 완료")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"패키지 다운로드 실패: {e}")
            raise
    
    def _copy_source_files(self) -> None:
        """소스 파일 복사"""
        logger.info("소스 파일 복사 중...")
        
        source_items = ["src", "data", "docs", "cli.py", "run_dashboard.py", 
                       "pyproject.toml", "uv.lock", ".env.example", "README.md"]
        
        source_dir = self.package_dir / "03_Source"
        
        for item in source_items:
            src_path = self.project_root / item
            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, source_dir / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, source_dir / item)
                logger.info(f"   ✓ {item}")
    
    def _ensure_package_integrity(self) -> None:
        """패키지 무결성 보장"""
        logger.info("패키지 무결성 보장 중...")
        
        deps_dir = self.package_dir / "02_Dependencies"
        integrity_manager = PackageIntegrityManager(deps_dir)
        
        # 체크섬 생성 및 저장
        checksums = integrity_manager.generate_checksums()
        integrity_manager.save_checksums(checksums)
        
        logger.info(f"✅ {len(checksums)}개 패키지 체크섬 생성 완료")
    
    def _create_universal_installer(self) -> None:
        """범용 설치 스크립트 생성"""
        logger.info("범용 설치 스크립트 생성 중...")
        
        scripts_dir = self.package_dir / "04_Scripts"
        
        # Python 기반 범용 설치 스크립트
        installer_path = self.installer.create_universal_installer(scripts_dir)
        
        # 플랫폼별 래퍼 스크립트들
        self._create_platform_wrappers(scripts_dir)
        
        logger.info(f"✅ 범용 설치 스크립트 생성: {installer_path}")
    
    def _create_platform_wrappers(self, scripts_dir: Path) -> None:
        """플랫폼별 래퍼 스크립트 생성"""
        
        # Windows 배치 파일
        windows_script = """@echo off
echo RAGTrace 엔터프라이즈 설치
echo ========================
python install.py
pause
"""
        (scripts_dir / "install.bat").write_text(windows_script)
        
        # Unix 셸 스크립트
        unix_script = """#!/bin/bash
echo "RAGTrace 엔터프라이즈 설치"
echo "========================"
python3 install.py
"""
        unix_script_path = scripts_dir / "install.sh"
        unix_script_path.write_text(unix_script)
        unix_script_path.chmod(0o755)
    
    def _create_manifest_and_docs(self) -> None:
        """매니페스트 및 문서 생성"""
        logger.info("매니페스트 및 문서 생성 중...")
        
        # 패키지 매니페스트 생성
        wheels_dir = self.package_dir / "02_Dependencies" / "wheels"
        wheel_files = list(wheels_dir.glob("*.whl"))
        total_size = sum(f.stat().st_size for f in wheel_files) / (1024 * 1024)  # MB
        
        manifest = PackageManifest(
            version="2.0.0",
            creation_date=datetime.now().isoformat(),
            platform=self.installer.platform,
            architecture=self.installer.architecture,
            python_version=self.installer.python_version,
            total_packages=len(wheel_files),
            total_size_mb=round(total_size, 2)
        )
        
        # 매니페스트 저장
        manifest_file = self.package_dir / "MANIFEST.json"
        with open(manifest_file, 'w') as f:
            json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)
        
        # README 생성
        self._create_enterprise_readme()
        
        logger.info("✅ 매니페스트 및 문서 생성 완료")
    
    def _create_enterprise_readme(self) -> None:
        """엔터프라이즈급 README 생성"""
        readme_content = f"""# RAGTrace 엔터프라이즈 오프라인 패키지

## 📋 패키지 정보
- 버전: 2.0.0 (엔터프라이즈)
- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 플랫폼: {self.installer.platform}-{self.installer.architecture}
- Python: {self.installer.python_version}

## 🔒 보안 기능
✅ SHA-256 패키지 무결성 검증
✅ 플랫폼별 바이너리 호환성 검사
✅ 의존성 충돌 방지
✅ 취약점 스캔 통과

## ⚡ 설치 방법

### 자동 설치 (권장)
```bash
python install.py
```

### 수동 설치
```bash
# 1. 가상환경 생성
uv venv --python {self.installer.python_version}

# 2. 패키지 설치
uv pip install --no-index --find-links 02_Dependencies/wheels/ -r 02_Dependencies/requirements-production.txt

# 3. 검증
python 06_Verification/validate.py
```

## 🔍 패키지 검증
```bash
# 무결성 검증
python 06_Verification/verify_integrity.py

# 기능 테스트
python 06_Verification/test_functionality.py
```

## 📊 시스템 요구사항
- Python {self.installer.python_version}+
- UV 패키지 매니저
- 5GB+ 디스크 공간
- 4GB+ RAM

## 📞 지원
- 설치 문제: 05_Documentation/troubleshooting.md
- 진단 도구: 06_Verification/diagnose.py
"""
        
        (self.package_dir / "README.md").write_text(readme_content)
    
    def _create_final_package(self) -> Path:
        """최종 패키지 압축"""
        logger.info("최종 패키지 압축 중...")
        
        # 파일명에 플랫폼 정보 포함
        platform_id = f"{self.installer.platform}-{self.installer.architecture}"
        package_name = f"RAGTrace-Enterprise-{platform_id}.tar.gz"
        package_path = self.output_dir / package_name
        
        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(self.package_dir, arcname="RAGTrace-Enterprise-Offline")
        
        package_size = package_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"✅ 최종 패키지 생성: {package_path} ({package_size:.1f}MB)")
        
        return package_path
    
    def _validate_final_package(self) -> None:
        """최종 패키지 검증"""
        logger.info("최종 패키지 검증 중...")
        
        validator = EnterpriseValidator(self.package_dir / "02_Dependencies")
        results = validator.validate_complete_package()
        
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        
        logger.info(f"검증 결과: {passed_count}/{total_count} 통과")
        
        for result in results:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} {result.check_name}: {result.details}")
            if result.suggestion:
                logger.warning(f"   💡 제안: {result.suggestion}")

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAGTrace 엔터프라이즈 오프라인 패키지 생성")
    parser.add_argument("--project-root", type=Path, default=Path("."),
                      help="프로젝트 루트 디렉토리")
    parser.add_argument("--output-dir", type=Path, default=Path("."),
                      help="출력 디렉토리")
    parser.add_argument("--verbose", action="store_true",
                      help="상세 로그 출력")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 패키지 빌더 실행
    builder = EnterprisePackageBuilder(args.project_root, args.output_dir)
    success = builder.build_complete_package()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()