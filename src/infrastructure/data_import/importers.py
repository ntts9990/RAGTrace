"""
Data Import Adapters

다양한 데이터 형식을 기존 EvaluationData 형식으로 변환하는 어댑터들.
기존 JSON 기반 시스템과 완전 호환됩니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import json
from pathlib import Path

from ...domain.entities.evaluation_data import EvaluationData


class DataImporter(ABC):
    """데이터 Import 기본 인터페이스"""
    
    @abstractmethod
    def import_data(self, file_path: Union[str, Path]) -> List[EvaluationData]:
        """파일에서 데이터를 읽어 EvaluationData 리스트로 변환"""
        pass
    
    @abstractmethod
    def validate_format(self, file_path: Union[str, Path]) -> bool:
        """파일 형식이 올바른지 검증"""
        pass


class ExcelImporter(DataImporter):
    """Excel 파일(.xlsx, .xls) Import 어댑터"""
    
    def __init__(self, sheet_name: Optional[str] = None):
        """
        Args:
            sheet_name: 읽을 시트 이름 (None이면 첫 번째 시트)
        """
        self.sheet_name = sheet_name or 0
        self.required_columns = ['question', 'contexts', 'answer', 'ground_truth']
    
    def import_data(self, file_path: Union[str, Path]) -> List[EvaluationData]:
        """Excel 파일에서 데이터 Import"""
        try:
            # Excel 파일 읽기
            df = pd.read_excel(file_path, sheet_name=self.sheet_name)
            
            # 필수 컬럼 확인
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
            
            # EvaluationData 리스트로 변환
            evaluation_data_list = []
            for _, row in df.iterrows():
                # contexts 처리 (문자열이면 JSON으로 파싱, 리스트면 그대로)
                contexts = self._parse_contexts(row['contexts'])
                
                evaluation_data = EvaluationData(
                    question=str(row['question']).strip(),
                    contexts=contexts,
                    answer=str(row['answer']).strip(),
                    ground_truth=str(row['ground_truth']).strip()
                )
                evaluation_data_list.append(evaluation_data)
            
            return evaluation_data_list
            
        except Exception as e:
            raise ImportError(f"Excel 파일 읽기 실패: {str(e)}")
    
    def validate_format(self, file_path: Union[str, Path]) -> bool:
        """Excel 파일 형식 검증"""
        try:
            file_path = Path(file_path)
            
            # 파일 확장자 검사
            if file_path.suffix.lower() not in ['.xlsx', '.xls']:
                return False
            
            # 파일 읽기 테스트
            df = pd.read_excel(file_path, sheet_name=self.sheet_name, nrows=1)
            
            # 필수 컬럼 존재 확인
            return all(col in df.columns for col in self.required_columns)
            
        except Exception:
            return False
    
    def _parse_contexts(self, contexts_value: Any) -> List[str]:
        """contexts 값을 List[str]로 변환"""
        if isinstance(contexts_value, str):
            # JSON 문자열인 경우 파싱 시도
            contexts_value = contexts_value.strip()
            if contexts_value.startswith('[') and contexts_value.endswith(']'):
                try:
                    parsed = json.loads(contexts_value)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except json.JSONDecodeError:
                    pass
            
            # 세미콜론이나 구분자로 분리된 경우
            if ';' in contexts_value:
                return [ctx.strip() for ctx in contexts_value.split(';') if ctx.strip()]
            elif '|' in contexts_value:
                return [ctx.strip() for ctx in contexts_value.split('|') if ctx.strip()]
            else:
                # 단일 문자열인 경우
                return [contexts_value]
        
        elif isinstance(contexts_value, list):
            return [str(item).strip() for item in contexts_value]
        
        else:
            # 기타 타입인 경우 문자열로 변환
            return [str(contexts_value).strip()]


class CSVImporter(DataImporter):
    """CSV 파일 Import 어댑터"""
    
    def __init__(self, encoding: str = 'utf-8', delimiter: str = ','):
        """
        Args:
            encoding: 파일 인코딩 (utf-8, cp949 등)
            delimiter: 구분자 (기본값: 쉼표)
        """
        self.encoding = encoding
        self.delimiter = delimiter
        self.required_columns = ['question', 'contexts', 'answer', 'ground_truth']
    
    def import_data(self, file_path: Union[str, Path]) -> List[EvaluationData]:
        """CSV 파일에서 데이터 Import"""
        try:
            # CSV 파일 읽기 (인코딩 자동 감지 시도)
            df = self._read_csv_with_encoding(file_path)
            
            # 필수 컬럼 확인
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"필수 컬럼이 누락되었습니다: {missing_columns}")
            
            # EvaluationData 리스트로 변환
            evaluation_data_list = []
            for _, row in df.iterrows():
                # contexts 처리
                contexts = self._parse_contexts(row['contexts'])
                
                evaluation_data = EvaluationData(
                    question=str(row['question']).strip(),
                    contexts=contexts,
                    answer=str(row['answer']).strip(),
                    ground_truth=str(row['ground_truth']).strip()
                )
                evaluation_data_list.append(evaluation_data)
            
            return evaluation_data_list
            
        except Exception as e:
            raise ImportError(f"CSV 파일 읽기 실패: {str(e)}")
    
    def validate_format(self, file_path: Union[str, Path]) -> bool:
        """CSV 파일 형식 검증"""
        try:
            file_path = Path(file_path)
            
            # 파일 확장자 검사
            if file_path.suffix.lower() != '.csv':
                return False
            
            # 파일 읽기 테스트
            df = self._read_csv_with_encoding(file_path, nrows=1)
            
            # 필수 컬럼 존재 확인
            return all(col in df.columns for col in self.required_columns)
            
        except Exception:
            return False
    
    def _read_csv_with_encoding(self, file_path: Union[str, Path], nrows: Optional[int] = None) -> pd.DataFrame:
        """인코딩을 자동 감지하여 CSV 파일 읽기"""
        encodings_to_try = [self.encoding, 'utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings_to_try:
            try:
                return pd.read_csv(
                    file_path, 
                    encoding=encoding, 
                    delimiter=self.delimiter,
                    nrows=nrows
                )
            except UnicodeDecodeError:
                continue
        
        # 모든 인코딩 실패 시 마지막 시도
        raise ImportError(f"지원되는 인코딩으로 파일을 읽을 수 없습니다: {encodings_to_try}")
    
    def _parse_contexts(self, contexts_value: Any) -> List[str]:
        """contexts 값을 List[str]로 변환 (Excel과 동일한 로직)"""
        if isinstance(contexts_value, str):
            contexts_value = contexts_value.strip()
            if contexts_value.startswith('[') and contexts_value.endswith(']'):
                try:
                    parsed = json.loads(contexts_value)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except json.JSONDecodeError:
                    pass
            
            # 구분자로 분리된 경우
            if ';' in contexts_value:
                return [ctx.strip() for ctx in contexts_value.split(';') if ctx.strip()]
            elif '|' in contexts_value:
                return [ctx.strip() for ctx in contexts_value.split('|') if ctx.strip()]
            else:
                return [contexts_value]
        
        elif isinstance(contexts_value, list):
            return [str(item).strip() for item in contexts_value]
        
        else:
            return [str(contexts_value).strip()]


class ImporterFactory:
    """Import 어댑터 팩토리"""
    
    @staticmethod
    def create_importer(file_path: Union[str, Path]) -> DataImporter:
        """파일 확장자에 따라 적절한 Import 어댑터 생성"""
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        if suffix in ['.xlsx', '.xls']:
            return ExcelImporter()
        elif suffix == '.csv':
            return CSVImporter()
        else:
            raise ValueError(f"지원되지 않는 파일 형식입니다: {suffix}")
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """지원되는 파일 형식 목록 반환"""
        return ['.xlsx', '.xls', '.csv']