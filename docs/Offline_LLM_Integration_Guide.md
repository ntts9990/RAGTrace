# 폐쇄망 환경에서의 LLM 및 임베딩 모델 통합 가이드

## 목차

1. [개요](#1-개요)
2. [폐쇄망 환경 요구사항](#2-폐쇄망-환경-요구사항)
3. [HCX-005 모델 통합](#3-hcx-005-모델-통합)
4. [BGE-M3 임베딩 모델 통합](#4-bge-m3-임베딩-모델-통합)
5. [오프라인 의존성 설치](#5-오프라인-의존성-설치)
6. [네트워크 격리 환경 설정](#6-네트워크-격리-환경-설정)
7. [성능 최적화](#7-성능-최적화)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 개요

이 문서는 외부 인터넷 접속이 제한된 폐쇄망(Air-gapped) 환경에서 RAGTrace 프로젝트에 다음 모델들을 통합하는 방법을 설명합니다:

- **LLM**: HyperCLOVA X HCX-005 모델
- **임베딩**: BGE-M3 다국어 임베딩 모델

### 1.1 폐쇄망 환경의 특징

- 외부 인터넷 연결 불가
- 모델 파일 로컬 저장 필요
- API 키 기반 외부 서비스 사용 불가
- 모든 의존성 사전 설치 필요

### 1.2 아키텍처 접근법

RAGTrace의 Hexagonal Architecture를 활용하여:
- 기존 코드 변경 최소화
- 새로운 어댑터 추가로 모델 통합
- 런타임 모델 교체 지원

---

## 2. 폐쇄망 환경 요구사항

### 2.1 하드웨어 요구사항

```yaml
최소 사양:
  CPU: 8코어 이상
  RAM: 32GB 이상
  Storage: 100GB 이상 (모델 파일 저장용)
  GPU: NVIDIA RTX 3080 이상 (선택사항, 성능 향상용)

권장 사양:
  CPU: 16코어 이상
  RAM: 64GB 이상
  Storage: 500GB 이상 SSD
  GPU: NVIDIA RTX 4090 또는 A100
```

### 2.2 소프트웨어 요구사항

```bash
# 기본 환경
Python 3.11+
CUDA 11.8+ (NVIDIA GPU 사용 시)
Docker 20.10+ (컨테이너 환경 시)

# 필수 라이브러리 (오프라인 설치 필요)
torch>=2.0.0
transformers>=4.36.0
sentence-transformers>=2.2.2

# GPU 가속 지원
CUDA: NVIDIA GPU (RTX 시리즈, Tesla, A100 등)
MPS: Apple Silicon (M1, M2, M3 Pro/Max/Ultra)
CPU: 모든 x86_64, ARM64 프로세서
```

### 2.3 모델 파일 다운로드 (인터넷 연결 환경에서 사전 준비)

```bash
# 별도 인터넷 연결 시스템에서 모델 다운로드
mkdir -p /models/bge-m3
mkdir -p /models/hcx-005

# BGE-M3 모델 다운로드
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='BAAI/bge-m3',
    local_dir='/models/bge-m3',
    local_dir_use_symlinks=False
)
"

# HCX-005 모델 파일 (NAVER Cloud Platform에서 다운로드)
# 실제 환경에서는 NAVER에서 제공하는 모델 파일을 다운로드
```

---

## 3. HCX-005 모델 통합

### 3.1 HCX-005 어댑터 구현

`src/infrastructure/llm/hcx_offline_adapter.py` 파일 생성:

```python
"""
폐쇄망 환경에서의 HCX-005 모델 어댑터
로컬에 저장된 모델 파일을 사용하여 추론 수행
"""

import os
import json
import torch
from typing import List, Optional, Dict, Any
from pathlib import Path

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextGenerationPipeline,
    GenerationConfig
)
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult, Generation

from src.application.ports.llm import LlmPort


class HCXOfflineAdapter(LlmPort):
    """폐쇄망 환경에서 HCX-005 모델을 사용하기 위한 어댑터"""
    
    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        max_length: int = 4096,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ):
        """
        Args:
            model_path: 로컬에 저장된 HCX-005 모델 경로
            device: 사용할 디바이스 ("cpu", "cuda", "auto")
            max_length: 최대 생성 토큰 수
            temperature: 생성 온도 (0.0-1.0)
            top_p: Nucleus sampling 파라미터
        """
        self.model_path = Path(model_path)
        self.device = self._get_device(device)
        self.max_length = max_length
        self.temperature = temperature
        self.top_p = top_p
        
        # 모델 로딩
        print(f"🔄 HCX-005 모델 로딩 중... ({self.model_path})")
        self._load_model()
        print(f"✅ HCX-005 모델 로딩 완료")
        
    def _get_device(self, device: str) -> str:
        """사용할 디바이스 결정"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """로컬 모델 파일 로딩"""
        try:
            # 토크나이저 로딩
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=True,
                trust_remote_code=True
            )
            
            # 모델 로딩
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                local_files_only=True,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map=self.device if self.device == "cuda" else None
            )
            
            # 생성 설정
            self.generation_config = GenerationConfig(
                max_length=self.max_length,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # 파이프라인 생성
            self.pipeline = TextGenerationPipeline(
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
        except Exception as e:
            raise RuntimeError(f"HCX-005 모델 로딩 실패: {e}")
    
    def generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        주어진 질문과 컨텍스트를 바탕으로 답변 생성
        
        Args:
            question: 사용자 질문
            contexts: 관련 컨텍스트 리스트
            
        Returns:
            생성된 답변
        """
        prompt = self._create_prompt(question, contexts)
        
        try:
            # 토큰화
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.to("cuda")
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    generation_config=self.generation_config,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 응답 추출
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.shape[1]:], 
                skip_special_tokens=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            print(f"❌ HCX-005 답변 생성 실패: {e}")
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    def get_llm(self) -> BaseLLM:
        """LangChain 호환 LLM 객체 반환"""
        return HCXLangChainLLM(self)
    
    def _create_prompt(self, question: str, contexts: List[str]) -> str:
        """HCX-005에 최적화된 프롬프트 생성"""
        context_text = "\n".join(f"참고자료 {i+1}: {ctx}" for i, ctx in enumerate(contexts))
        
        prompt = f"""다음 참고자료를 바탕으로 질문에 대한 정확하고 유용한 답변을 제공해주세요.

참고자료:
{context_text}

질문: {question}

답변: """
        return prompt
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "HCX-005",
            "model_path": str(self.model_path),
            "device": self.device,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p
        }


class HCXLangChainLLM(BaseLLM):
    """LangChain 호환을 위한 HCX-005 래퍼"""
    
    def __init__(self, hcx_adapter: HCXOfflineAdapter):
        super().__init__()
        self.hcx_adapter = hcx_adapter
    
    @property
    def _llm_type(self) -> str:
        return "hcx-005-offline"
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """프롬프트 리스트에 대한 생성 결과 반환"""
        generations = []
        
        for prompt in prompts:
            try:
                # HCX 어댑터를 사용하여 직접 생성 (컨텍스트 없이)
                result = self._generate_single(prompt)
                generations.append([Generation(text=result)])
            except Exception as e:
                generations.append([Generation(text=f"생성 실패: {str(e)}")])
        
        return LLMResult(generations=generations)
    
    def _generate_single(self, prompt: str) -> str:
        """단일 프롬프트에 대한 생성"""
        inputs = self.hcx_adapter.tokenizer.encode(prompt, return_tensors="pt")
        if self.hcx_adapter.device == "cuda":
            inputs = inputs.to("cuda")
        
        with torch.no_grad():
            outputs = self.hcx_adapter.model.generate(
                inputs,
                generation_config=self.hcx_adapter.generation_config
            )
        
        generated_text = self.hcx_adapter.tokenizer.decode(
            outputs[0][inputs.shape[1]:], 
            skip_special_tokens=True
        )
        
        return generated_text.strip()
```

### 3.2 HCX-005 설정 파일

`config/hcx_config.yaml` 생성:

```yaml
# HCX-005 오프라인 모델 설정
hcx_offline:
  model_path: "/models/hcx-005"  # 로컬 모델 저장 경로
  device: "auto"                 # "cpu", "cuda", "auto"
  generation:
    max_length: 4096
    temperature: 0.7
    top_p: 0.9
    repetition_penalty: 1.1
  
  # 메모리 최적화 설정
  optimization:
    use_flash_attention: true
    gradient_checkpointing: true
    load_in_8bit: false          # 메모리 부족 시 true로 설정
    load_in_4bit: false          # 극도의 메모리 절약 필요 시
  
  # 배치 처리 설정
  batch_processing:
    max_batch_size: 4
    enable_batching: true
```

---

## 4. BGE-M3 임베딩 모델 통합

### 4.1 BGE-M3 어댑터 구현

`src/infrastructure/embeddings/bge_m3_offline_adapter.py` 파일 생성:

```python
"""
폐쇄망 환경에서의 BGE-M3 임베딩 모델 어댑터
로컬에 저장된 모델 파일을 사용하여 임베딩 생성
"""

import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from FlagEmbedding import BGEM3FlagModel
from langchain_core.embeddings import Embeddings

from src.application.ports.embedding import EmbeddingPort


class BGEM3OfflineAdapter(EmbeddingPort, Embeddings):
    """폐쇄망 환경에서 BGE-M3 모델을 사용하기 위한 어댑터"""
    
    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        use_fp16: bool = True,
        max_length: int = 8192,
        batch_size: int = 12,
        normalize_embeddings: bool = True,
        **kwargs
    ):
        """
        Args:
            model_path: 로컬에 저장된 BGE-M3 모델 경로
            device: 사용할 디바이스 ("cpu", "cuda", "auto")
            use_fp16: FP16 정밀도 사용 여부 (GPU에서 성능 향상)
            max_length: 최대 토큰 길이 (BGE-M3는 최대 8192 지원)
            batch_size: 배치 크기
            normalize_embeddings: 임베딩 정규화 여부
        """
        self.model_path = Path(model_path)
        self.device = self._get_device(device)
        self.use_fp16 = use_fp16 and self.device == "cuda"
        self.max_length = max_length
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        
        # 모델 로딩
        print(f"🔄 BGE-M3 임베딩 모델 로딩 중... ({self.model_path})")
        self._load_model()
        print(f"✅ BGE-M3 임베딩 모델 로딩 완료")
        
    def _get_device(self, device: str) -> str:
        """사용할 디바이스 결정"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """로컬 BGE-M3 모델 로딩"""
        try:
            self.model = BGEM3FlagModel(
                str(self.model_path),
                use_fp16=self.use_fp16,
                device=self.device,
                max_length=self.max_length,
                normalize_embeddings=self.normalize_embeddings
            )
            
            # 모델 정보 확인
            print(f"📊 BGE-M3 모델 정보:")
            print(f"   - 디바이스: {self.device}")
            print(f"   - FP16 사용: {self.use_fp16}")
            print(f"   - 최대 길이: {self.max_length}")
            print(f"   - 배치 크기: {self.batch_size}")
            
        except Exception as e:
            raise RuntimeError(f"BGE-M3 모델 로딩 실패: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        문서 리스트를 임베딩으로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        try:
            # BGE-M3의 dense 임베딩 사용
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                max_length=self.max_length
            )['dense_vecs']
            
            return embeddings.tolist()
            
        except Exception as e:
            print(f"❌ 문서 임베딩 생성 실패: {e}")
            # 오류 시 영벡터 반환
            return [[0.0] * 1024 for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """
        단일 쿼리를 임베딩으로 변환
        
        Args:
            text: 임베딩할 쿼리 텍스트
            
        Returns:
            임베딩 벡터
        """
        try:
            # BGE-M3는 쿼리와 문서에 동일한 방식 사용 (instruction 불필요)
            embedding = self.model.encode(
                [text],
                batch_size=1,
                max_length=self.max_length
            )['dense_vecs'][0]
            
            return embedding.tolist()
            
        except Exception as e:
            print(f"❌ 쿼리 임베딩 생성 실패: {e}")
            return [0.0] * 1024
    
    def get_multi_embeddings(
        self, 
        texts: List[str], 
        return_dense: bool = True,
        return_sparse: bool = False,
        return_colbert_vecs: bool = False
    ) -> Dict[str, Any]:
        """
        BGE-M3의 다중 임베딩 기능 사용
        
        Args:
            texts: 임베딩할 텍스트 리스트
            return_dense: Dense 임베딩 반환 여부
            return_sparse: Sparse 임베딩 반환 여부
            return_colbert_vecs: ColBERT 스타일 벡터 반환 여부
            
        Returns:
            다양한 타입의 임베딩 딕셔너리
        """
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                max_length=self.max_length,
                return_dense=return_dense,
                return_sparse=return_sparse,
                return_colbert_vecs=return_colbert_vecs
            )
            
            return embeddings
            
        except Exception as e:
            print(f"❌ 다중 임베딩 생성 실패: {e}")
            return {"dense_vecs": np.zeros((len(texts), 1024))}
    
    def compute_similarity(
        self, 
        query_embedding: List[float], 
        doc_embeddings: List[List[float]]
    ) -> List[float]:
        """
        쿼리와 문서 임베딩 간 유사도 계산
        
        Args:
            query_embedding: 쿼리 임베딩
            doc_embeddings: 문서 임베딩 리스트
            
        Returns:
            유사도 점수 리스트
        """
        try:
            query_vec = np.array(query_embedding)
            doc_vecs = np.array(doc_embeddings)
            
            # 코사인 유사도 계산
            similarities = np.dot(doc_vecs, query_vec) / (
                np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
            )
            
            return similarities.tolist()
            
        except Exception as e:
            print(f"❌ 유사도 계산 실패: {e}")
            return [0.0] * len(doc_embeddings)
    
    def get_embedding_dimension(self) -> int:
        """임베딩 차원 수 반환"""
        return 1024  # BGE-M3 기본 차원
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": "BGE-M3",
            "model_path": str(self.model_path),
            "device": self.device,
            "use_fp16": self.use_fp16,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "embedding_dimension": self.get_embedding_dimension(),
            "features": [
                "Multi-lingual (100+ languages)",
                "Multi-granularity (up to 8192 tokens)",
                "Multi-functionality (dense, sparse, colbert)"
            ]
        }
```

### 4.2 BGE-M3 설정 파일

`config/bge_m3_config.yaml` 생성:

```yaml
# BGE-M3 오프라인 임베딩 설정
bge_m3_offline:
  model_path: "/models/bge-m3"   # 로컬 모델 저장 경로
  device: "auto"                 # "cpu", "cuda", "auto"
  
  # 성능 설정
  performance:
    use_fp16: true               # GPU에서 FP16 사용
    batch_size: 12               # 배치 크기 (메모리에 따라 조정)
    max_length: 8192             # 최대 토큰 길이
    normalize_embeddings: true   # 임베딩 정규화
  
  # 다중 기능 설정
  multi_functionality:
    return_dense: true           # Dense 임베딩 반환
    return_sparse: false         # Sparse 임베딩 반환 (필요시 true)
    return_colbert_vecs: false   # ColBERT 벡터 반환 (필요시 true)
  
  # 메모리 최적화
  optimization:
    enable_cache: true           # 임베딩 캐싱
    cache_size: 10000           # 캐시 최대 항목 수
    clear_cache_interval: 1000   # 캐시 정리 주기
```

---

## 5. 오프라인 의존성 설치

### 5.1 의존성 패키지 다운로드 (인터넷 연결 환경)

```bash
#!/bin/bash
# download_dependencies.sh - 의존성 패키지 다운로드 스크립트

# 패키지 다운로드 디렉토리 생성
mkdir -p offline_packages

# 핵심 패키지 다운로드
pip download -d offline_packages \
    torch==2.1.0 \
    transformers==4.36.0 \
    sentence-transformers==2.2.2 \
    FlagEmbedding==1.2.0 \
    numpy==1.24.3 \
    scipy==1.11.3 \
    scikit-learn==1.3.0 \
    huggingface_hub==0.19.0 \
    tokenizers==0.15.0 \
    accelerate==0.25.0 \
    safetensors==0.4.0

# GPU 지원 패키지 (CUDA 11.8)
pip download -d offline_packages \
    torch==2.1.0+cu118 \
    torchvision==0.16.0+cu118 \
    torchaudio==2.1.0+cu118 \
    --extra-index-url https://download.pytorch.org/whl/cu118

# 압축
tar -czf offline_packages.tar.gz offline_packages/
```

### 5.2 폐쇄망에서의 패키지 설치

```bash
#!/bin/bash
# install_offline.sh - 폐쇄망에서 패키지 설치

# 패키지 압축 해제
tar -xzf offline_packages.tar.gz

# 오프라인 설치
pip install --no-index --find-links offline_packages/ \
    torch transformers sentence-transformers \
    FlagEmbedding numpy scipy scikit-learn \
    huggingface_hub tokenizers accelerate safetensors

# 설치 확인
python -c "
import torch
import transformers
from FlagEmbedding import BGEM3FlagModel
print('✅ 모든 패키지 설치 완료')
print(f'PyTorch 버전: {torch.__version__}')
print(f'Transformers 버전: {transformers.__version__}')
print(f'CUDA 사용 가능: {torch.cuda.is_available()}')
"
```

### 5.3 UV를 이용한 오프라인 설치

```bash
# pyproject.toml에 로컬 패키지 경로 추가
[tool.uv]
index-url = "file:///path/to/offline_packages"
extra-index-urls = []

# 오프라인 설치
uv sync --offline --no-network
```

---

## 6. 네트워크 격리 환경 설정

### 6.1 환경 설정 파일

`.env.offline` 파일 생성:

```bash
# 폐쇄망 환경 설정
ENVIRONMENT=offline
NETWORK_MODE=isolated

# 로컬 모델 경로
HCX_MODEL_PATH=/models/hcx-005
BGE_M3_MODEL_PATH=/models/bge-m3

# 디바이스 설정
DEVICE=auto  # auto, cpu, cuda
USE_GPU=true

# 캐싱 설정
ENABLE_MODEL_CACHE=true
CACHE_DIR=/cache/ragtrace

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=/logs/ragtrace.log

# API 설정 (오프라인에서는 비활성화)
ENABLE_EXTERNAL_API=false
GEMINI_API_KEY=""
CLOVA_STUDIO_API_KEY=""
```

### 6.2 컨테이너 초기화 스크립트

`scripts/init_offline_container.py`:

```python
#!/usr/bin/env python3
"""
폐쇄망 환경에서 RAGTrace 컨테이너 초기화 스크립트
"""

import os
import sys
import json
import logging
from pathlib import Path

def check_offline_requirements():
    """오프라인 환경 요구사항 확인"""
    print("🔍 폐쇄망 환경 요구사항 확인 중...")
    
    # 모델 파일 확인
    hcx_path = Path(os.getenv("HCX_MODEL_PATH", "/models/hcx-005"))
    bge_path = Path(os.getenv("BGE_M3_MODEL_PATH", "/models/bge-m3"))
    
    if not hcx_path.exists():
        print(f"❌ HCX-005 모델 파일이 없습니다: {hcx_path}")
        return False
    
    if not bge_path.exists():
        print(f"❌ BGE-M3 모델 파일이 없습니다: {bge_path}")
        return False
    
    # 필수 파일 확인
    required_files = {
        "HCX-005": ["config.json", "pytorch_model.bin", "tokenizer.json"],
        "BGE-M3": ["config.json", "pytorch_model.bin", "tokenizer.json"]
    }
    
    for model_name, model_path in [("HCX-005", hcx_path), ("BGE-M3", bge_path)]:
        for file_name in required_files[model_name]:
            file_path = model_path / file_name
            if not file_path.exists():
                print(f"❌ {model_name} 필수 파일 누락: {file_path}")
                return False
    
    print("✅ 모든 모델 파일 확인 완료")
    return True

def setup_offline_models():
    """오프라인 모델 설정"""
    print("🔧 오프라인 모델 설정 중...")
    
    try:
        # HCX-005 모델 테스트
        from src.infrastructure.llm.hcx_offline_adapter import HCXOfflineAdapter
        hcx_path = os.getenv("HCX_MODEL_PATH", "/models/hcx-005")
        hcx_adapter = HCXOfflineAdapter(hcx_path)
        print("✅ HCX-005 모델 로딩 성공")
        
        # BGE-M3 모델 테스트
        from src.infrastructure.embeddings.bge_m3_offline_adapter import BGEM3OfflineAdapter
        bge_path = os.getenv("BGE_M3_MODEL_PATH", "/models/bge-m3")
        bge_adapter = BGEM3OfflineAdapter(bge_path)
        print("✅ BGE-M3 모델 로딩 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 모델 설정 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 RAGTrace 폐쇄망 환경 초기화 시작")
    print("=" * 50)
    
    # 환경 변수 로드
    if os.path.exists(".env.offline"):
        from dotenv import load_dotenv
        load_dotenv(".env.offline")
        print("✅ 오프라인 환경 설정 로드 완료")
    
    # 요구사항 확인
    if not check_offline_requirements():
        print("❌ 요구사항 확인 실패")
        sys.exit(1)
    
    # 모델 설정
    if not setup_offline_models():
        print("❌ 모델 설정 실패")
        sys.exit(1)
    
    print("🎉 폐쇄망 환경 초기화 완료!")
    print("RAGTrace 서비스를 시작할 수 있습니다.")

if __name__ == "__main__":
    main()
```

### 6.3 Docker 오프라인 설정

`Dockerfile.offline`:

```dockerfile
# RAGTrace 폐쇄망 환경용 Dockerfile
FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 오프라인 패키지 복사 및 설치
COPY offline_packages/ /tmp/offline_packages/
RUN pip install --no-index --find-links /tmp/offline_packages/ \
    torch transformers sentence-transformers \
    FlagEmbedding numpy scipy scikit-learn \
    huggingface_hub tokenizers accelerate safetensors

# 모델 파일 복사
COPY models/ /models/

# 애플리케이션 코드 복사
COPY src/ /app/src/
COPY config/ /app/config/
COPY scripts/ /app/scripts/
COPY .env.offline /app/.env

# 초기화 스크립트 실행
RUN python scripts/init_offline_container.py

# 비루트 사용자 생성
RUN useradd -m -u 1000 ragtrace && \
    chown -R ragtrace:ragtrace /app /models

USER ragtrace

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV ENVIRONMENT=offline

EXPOSE 8501

CMD ["python", "src/presentation/main.py"]
```

---

## 7. 성능 최적화

### 7.1 메모리 최적화

```python
# scripts/optimize_memory.py
"""메모리 사용량 최적화 스크립트"""

import torch
import gc
from typing import Dict, Any

class MemoryOptimizer:
    """메모리 최적화 관리자"""
    
    @staticmethod
    def optimize_torch_settings():
        """PyTorch 메모리 설정 최적화"""
        if torch.cuda.is_available():
            # CUDA 메모리 관리 최적화
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            # 메모리 할당 전략 설정
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
            
        # CPU 스레드 최적화
        torch.set_num_threads(min(8, torch.get_num_threads()))
    
    @staticmethod
    def cleanup_memory():
        """메모리 정리"""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """메모리 사용량 정보 반환"""
        info = {
            "cpu_memory_gb": psutil.virtual_memory().used / (1024**3),
            "cpu_memory_percent": psutil.virtual_memory().percent
        }
        
        if torch.cuda.is_available():
            info.update({
                "gpu_memory_allocated_gb": torch.cuda.memory_allocated() / (1024**3),
                "gpu_memory_reserved_gb": torch.cuda.memory_reserved() / (1024**3),
                "gpu_memory_total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3)
            })
        
        return info
```

### 7.2 배치 처리 최적화

```python
# src/utils/batch_processor.py
"""배치 처리 최적화"""

from typing import List, Generator, TypeVar, Callable
import math

T = TypeVar('T')

class BatchProcessor:
    """효율적인 배치 처리를 위한 유틸리티"""
    
    @staticmethod
    def create_batches(items: List[T], batch_size: int) -> Generator[List[T], None, None]:
        """리스트를 배치로 분할"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
    
    @staticmethod
    def process_with_batches(
        items: List[T],
        processor: Callable[[List[T]], List[Any]],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[Any]:
        """배치 단위로 항목 처리"""
        results = []
        total_batches = math.ceil(len(items) / batch_size)
        
        for i, batch in enumerate(BatchProcessor.create_batches(items, batch_size)):
            if show_progress:
                print(f"배치 처리 중: {i+1}/{total_batches}")
            
            batch_results = processor(batch)
            results.extend(batch_results)
            
            # 메모리 정리
            if i % 10 == 0:  # 10배치마다 메모리 정리
                MemoryOptimizer.cleanup_memory()
        
        return results
```

### 7.3 캐싱 시스템

```python
# src/utils/embedding_cache.py
"""임베딩 캐싱 시스템"""

import pickle
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import sqlite3

class EmbeddingCache:
    """임베딩 결과 캐싱 시스템"""
    
    def __init__(self, cache_dir: str = "/cache/embeddings", max_entries: int = 10000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.db_path = self.cache_dir / "embeddings.db"
        self._init_db()
    
    def _init_db(self):
        """캐시 데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    text_hash TEXT PRIMARY KEY,
                    embedding_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _hash_text(self, text: str) -> str:
        """텍스트 해시 생성"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """캐시에서 임베딩 조회"""
        text_hash = self._hash_text(text)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT embedding_data FROM embeddings WHERE text_hash = ?",
                (text_hash,)
            )
            result = cursor.fetchone()
            
            if result:
                return pickle.loads(result[0])
        
        return None
    
    def set(self, text: str, embedding: List[float]):
        """캐시에 임베딩 저장"""
        text_hash = self._hash_text(text)
        embedding_data = pickle.dumps(embedding)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO embeddings (text_hash, embedding_data) VALUES (?, ?)",
                (text_hash, embedding_data)
            )
            
            # 캐시 크기 제한
            conn.execute("""
                DELETE FROM embeddings WHERE text_hash IN (
                    SELECT text_hash FROM embeddings 
                    ORDER BY created_at ASC 
                    LIMIT MAX(0, (SELECT COUNT(*) FROM embeddings) - ?)
                )
            """, (self.max_entries,))
    
    def clear(self):
        """캐시 전체 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM embeddings")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            count = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(LENGTH(embedding_data)) FROM embeddings")
            size_bytes = cursor.fetchone()[0] or 0
        
        return {
            "entry_count": count,
            "size_mb": size_bytes / (1024 * 1024),
            "max_entries": self.max_entries
        }
```

---

## 8. 트러블슈팅

### 8.1 일반적인 문제와 해결책

#### 모델 로딩 실패
```python
# 문제: CUDA out of memory
# 해결: 모델 로딩 시 메모리 최적화
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,  # 메모리 절약
    device_map="auto",          # 자동 디바이스 배치
    load_in_8bit=True,         # 8bit 양자화
    # load_in_4bit=True,       # 극도의 메모리 절약 필요 시
)
```

#### 토크나이저 오류
```python
# 문제: tokenizer.json not found
# 해결: 토크나이저 파일 확인 및 재다운로드
if not (model_path / "tokenizer.json").exists():
    print("토크나이저 파일 누락")
    # 백업 토크나이저 사용
    tokenizer = AutoTokenizer.from_pretrained(
        "bert-base-multilingual-cased",
        local_files_only=True
    )
```

#### 성능 저하
```python
# 문제: 느린 추론 속도
# 해결: 배치 처리 및 캐싱 활용
def optimize_inference():
    # 1. 배치 크기 조정
    batch_size = 4 if torch.cuda.is_available() else 1
    
    # 2. 컴파일 최적화 (PyTorch 2.0+)
    if hasattr(torch, 'compile'):
        model = torch.compile(model)
    
    # 3. 캐싱 활용
    cache = EmbeddingCache()
    
    return batch_size, model, cache
```

### 8.2 로그 설정

```python
# config/logging_config.py
"""오프라인 환경 로깅 설정"""

import logging
import sys
from pathlib import Path

def setup_offline_logging(log_level: str = "INFO", log_file: str = "/logs/ragtrace.log"):
    """오프라인 환경용 로깅 설정"""
    
    # 로그 디렉토리 생성
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 로깅 설정
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 특정 라이브러리 로그 레벨 조정
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("FlagEmbedding").setLevel(logging.INFO)
    
    logger = logging.getLogger("RAGTrace")
    logger.info("오프라인 환경 로깅 설정 완료")
    
    return logger
```

### 8.3 건강 상태 체크

```python
# scripts/health_check.py
"""시스템 건강 상태 체크 스크립트"""

import torch
import psutil
import time
from pathlib import Path

def check_system_health():
    """시스템 건강 상태 확인"""
    health_report = {
        "timestamp": time.time(),
        "status": "healthy",
        "issues": []
    }
    
    # CPU 사용률 확인
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 90:
        health_report["issues"].append(f"높은 CPU 사용률: {cpu_percent}%")
    
    # 메모리 사용률 확인
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        health_report["issues"].append(f"높은 메모리 사용률: {memory.percent}%")
    
    # GPU 메모리 확인 (사용 가능한 경우)
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
        if gpu_memory > 0.9:
            health_report["issues"].append(f"높은 GPU 메모리 사용률: {gpu_memory*100:.1f}%")
    
    # 모델 파일 확인
    model_paths = [
        Path("/models/hcx-005"),
        Path("/models/bge-m3")
    ]
    
    for path in model_paths:
        if not path.exists():
            health_report["issues"].append(f"모델 파일 누락: {path}")
    
    # 전체 상태 결정
    if health_report["issues"]:
        health_report["status"] = "warning" if len(health_report["issues"]) < 3 else "critical"
    
    return health_report

if __name__ == "__main__":
    report = check_system_health()
    print(f"시스템 상태: {report['status']}")
    if report['issues']:
        print("발견된 문제:")
        for issue in report['issues']:
            print(f"  - {issue}")
    else:
        print("모든 시스템 정상 작동 중")
```

---

## 결론

이 가이드를 통해 폐쇄망 환경에서 HCX-005 LLM과 BGE-M3 임베딩 모델을 성공적으로 통합할 수 있습니다. 주요 고려사항:

1. **사전 준비**: 모든 모델 파일과 의존성을 인터넷 연결 환경에서 미리 다운로드
2. **메모리 관리**: 제한된 리소스에서 효율적인 모델 운영을 위한 최적화
3. **캐싱 활용**: 반복적인 작업의 성능 향상을 위한 지능적 캐싱
4. **모니터링**: 시스템 건강 상태와 성능 지속적 모니터링

폐쇄망 환경의 특성상 문제 발생 시 외부 지원이 제한되므로, 충분한 테스트와 문서화가 중요합니다.