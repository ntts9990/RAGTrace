import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from src.application.ports.repository import EvaluationRepositoryPort
from src.domain import EvaluationData
from src.domain.exceptions import InvalidDataFormatError
from src.infrastructure.data_import.importers import ExcelImporter, CSVImporter


class FileRepositoryAdapter(EvaluationRepositoryPort):
    """파일 시스템에서 평가 데이터셋을 로드하는 구현체 (Adapter)"""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_data(self) -> List[EvaluationData]:
        """
        지정된 경로의 파일을 읽어 EvaluationData 객체 리스트로 변환합니다.
        JSON, Excel (.xlsx, .xls), CSV 파일을 지원합니다.
        
        Raises:
            InvalidDataFormatError: 파일 형식이나 데이터 구조에 문제가 있는 경우
        """
        file_path = Path(self.file_path)
        
        if not file_path.exists():
            raise InvalidDataFormatError(
                f"평가 데이터 파일을 찾을 수 없습니다: {self.file_path}",
                file_path=self.file_path
            )
        
        # 파일 확장자에 따라 적절한 importer 사용
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension in ['.xlsx', '.xls']:
                # Excel 파일 처리 - 이미 EvaluationData 객체 리스트를 반환
                importer = ExcelImporter()
                return importer.import_data(file_path)
            elif file_extension == '.csv':
                # CSV 파일 처리 - 이미 EvaluationData 객체 리스트를 반환
                importer = CSVImporter()
                return importer.import_data(file_path)
            else:
                # JSON 파일 처리 (기본) - dict 리스트이므로 아래에서 변환 필요
                try:
                    with open(self.file_path, encoding="utf-8") as f:
                        data = json.load(f)
                except json.JSONDecodeError as e:
                    raise InvalidDataFormatError(
                        f"JSON 파일 형식이 올바르지 않습니다: {str(e)}",
                        file_path=self.file_path,
                        line_number=getattr(e, 'lineno', None)
                    )
        except Exception as e:
            if isinstance(e, InvalidDataFormatError):
                raise
            raise InvalidDataFormatError(
                f"파일 읽기 실패: {str(e)}",
                file_path=self.file_path
            )
        
        if not isinstance(data, list):
            raise InvalidDataFormatError(
                "평가 데이터는 배열(array) 형태여야 합니다.",
                file_path=self.file_path
            )
        
        evaluation_data_list = []
        validation_errors = []
        
        for idx, item in enumerate(data):
            try:
                evaluation_data = EvaluationData(**item)
                evaluation_data_list.append(evaluation_data)
            except ValidationError as e:
                # 각 필드별 오류를 수집
                for error in e.errors():
                    field_path = " -> ".join(str(x) for x in error["loc"])
                    validation_errors.append({
                        "item_index": idx + 1,
                        "field": field_path,
                        "error": error["msg"],
                        "input_value": error.get("input", "N/A")
                    })
            except Exception as e:
                validation_errors.append({
                    "item_index": idx + 1,
                    "field": "전체",
                    "error": str(e),
                    "input_value": item
                })
        
        if validation_errors:
            # 구체적인 오류 메시지 생성
            error_details = []
            for error in validation_errors:
                error_details.append(
                    f"항목 {error['item_index']}: '{error['field']}' 필드 - {error['error']}"
                )
            
            error_message = f"데이터 유효성 검사 실패 ({len(validation_errors)}개 오류):\n" + \
                          "\n".join(error_details[:5])  # 처음 5개만 표시
            
            if len(validation_errors) > 5:
                error_message += f"\n... 그 외 {len(validation_errors) - 5}개 오류"
            
            raise InvalidDataFormatError(
                error_message,
                file_path=self.file_path
            )
        
        return evaluation_data_list
