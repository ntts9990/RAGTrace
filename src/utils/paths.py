"""중앙화된 경로 관리 모듈

이 모듈은 프로젝트의 모든 경로를 중앙에서 관리하여 하드코딩된 경로를 제거하고
환경에 독립적인 코드를 작성할 수 있도록 합니다.
"""

from pathlib import Path


def get_project_root() -> Path:
    """프로젝트의 루트 디렉토리를 동적으로 찾아서 반환합니다.

    pyproject.toml 파일이 존재하는 디렉토리를 프로젝트 루트로 판단합니다.

    Returns:
        Path: 프로젝트 루트 디렉토리의 Path 객체

    Raises:
        FileNotFoundError: 프로젝트 루트를 찾을 수 없을 때
    """
    current_path = Path(__file__).resolve()

    # 현재 파일에서 시작하여 상위 디렉토리로 이동하며 pyproject.toml 탐색
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists():
            return current_path
        current_path = current_path.parent

    raise FileNotFoundError(
        "프로젝트 루트를 찾을 수 없습니다. 'pyproject.toml' 파일이 존재하는지 확인해주세요."
    )


def ensure_directory_exists(path: Path) -> Path:
    """디렉토리가 존재하지 않으면 생성합니다.

    Args:
        path: 생성할 디렉토리 경로

    Returns:
        Path: 생성된 (또는 이미 존재하는) 디렉토리 경로
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


# 프로젝트 루트 경로 (모듈 로딩 시점에 계산)
PROJECT_ROOT = get_project_root()

# 주요 디렉토리 경로들
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 데이터 관련 경로들
DB_DIR = DATA_DIR / "db"
TEMP_DIR = DATA_DIR / "temp"

# 주요 파일 경로들
DATABASE_PATH = DB_DIR / "evaluations.db"
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# 기본 평가 데이터 파일들
DEFAULT_EVALUATION_DATA = DATA_DIR / "evaluation_data.json"
VARIANT1_EVALUATION_DATA = DATA_DIR / "evaluation_data_variant1.json"

# 데이터 파일 매핑 (variant 처리 용이성을 위한 딕셔너리)
EVALUATION_DATA_FILES = {
    "evaluation_data.json": DEFAULT_EVALUATION_DATA,
    "evaluation_data_variant1.json": VARIANT1_EVALUATION_DATA,
    "default": DEFAULT_EVALUATION_DATA,
}


def get_evaluation_data_path(dataset_name: str) -> Path | None:
    """평가 데이터 파일의 경로를 반환합니다.

    Args:
        dataset_name: 데이터셋 파일명 또는 식별자

    Returns:
        Path: 데이터 파일 경로 (파일이 존재하지 않으면 None)
    """
    # 1. 절대 경로인 경우 처리
    dataset_path = Path(dataset_name)
    if dataset_path.is_absolute() and dataset_path.exists():
        return dataset_path
    
    # 1.5. 상대 경로지만 그대로 존재하는 경우 (quick-eval 변환 파일 등)
    if dataset_path.exists():
        return dataset_path
    
    # 2. 정확한 파일명으로 먼저 확인 (기존 매핑)
    if dataset_name in EVALUATION_DATA_FILES:
        file_path = EVALUATION_DATA_FILES[dataset_name]
        if file_path.exists():
            return file_path
    
    # 3. data/ 디렉토리에서 직접 파일명 확인
    file_path = DATA_DIR / dataset_name
    if file_path.exists():
        return file_path
    
    # 4. 확장자가 없는 경우 .json 추가해서 확인
    if not dataset_name.endswith('.json'):
        json_path = DATA_DIR / f"{dataset_name}.json"
        if json_path.exists():
            return json_path
    
    # 5. variant 키워드가 포함된 경우 처리 (호환성 유지)
    if "variant1" in dataset_name.lower():
        file_path = VARIANT1_EVALUATION_DATA
        if file_path.exists():
            return file_path
    
    # 6. evaluation_data로 시작하는 경우 처리 (호환성 유지)
    if dataset_name.startswith("evaluation_data") and not dataset_name.endswith('.json'):
        json_path = DATA_DIR / f"{dataset_name}.json"
        if json_path.exists():
            return json_path

    return None


def get_available_datasets() -> list[str]:
    """사용 가능한 평가 데이터셋 목록을 반환합니다.
    JSON, CSV, Excel 파일을 모두 포함합니다.

    Returns:
        list: 존재하는 데이터 파일명 목록
    """
    available = []
    
    # 지원하는 파일 확장자
    supported_extensions = ['.json', '.csv', '.xlsx', '.xls']
    
    # data/ 디렉토리의 모든 지원 파일 검색
    if DATA_DIR.exists():
        for extension in supported_extensions:
            for data_file in DATA_DIR.glob(f"*{extension}"):
                # 숨김 파일이나 임시 파일 제외
                if not data_file.name.startswith('.') and not data_file.name.startswith('~'):
                    available.append(data_file.name)
    
    # 정렬해서 반환
    return sorted(available)


# 초기화: 필수 디렉토리 생성
def _initialize_directories():
    """프로젝트 실행에 필요한 디렉토리들을 생성합니다."""
    for directory in [DATA_DIR, DB_DIR, TEMP_DIR]:
        ensure_directory_exists(directory)


# 모듈 로딩 시 디렉토리 초기화 실행
_initialize_directories()
