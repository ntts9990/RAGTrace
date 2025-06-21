"""
BGE-M3 로컬 임베딩 모델 어댑터
sentence-transformers를 사용한 로컬 임베딩 처리
CUDA GPU 자동 감지 및 최적화 지원
"""

import os
import time
import platform
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from src.config import SUPPORTED_DEVICE_TYPES


class BgeM3EmbeddingAdapter(Embeddings):
    """BGE-M3 로컬 임베딩 모델 어댑터 (GPU 자동 감지)"""
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        BGE-M3 모델을 초기화합니다.
        
        Args:
            model_path: 로컬 모델 경로 (None이면 자동 다운로드)
            device: 실행 디바이스 (None이면 자동 감지, "cpu", "cuda", "mps")
        """
        self.model_path = model_path or "BAAI/bge-m3"
        self.device = self._detect_best_device(device)
        self.model = None
        self.device_info = {}
        
        # 로컬 모델 경로 확인
        if model_path and os.path.exists(model_path):
            print(f"✅ 로컬 BGE-M3 모델 경로 확인: {model_path}")
        elif model_path:
            print(f"⚠️ 지정된 모델 경로가 존재하지 않음: {model_path}")
            print("📥 Hugging Face에서 모델을 다운로드합니다...")
        else:
            print("📥 BGE-M3 모델을 자동 다운로드합니다...")
        
        # 모델 로드 (지연 로딩)
        self._load_model()
    
    def _detect_best_device(self, preferred_device: Optional[str] = None) -> str:
        """최적의 디바이스를 자동 감지합니다."""
        if preferred_device:
            # 사용자가 명시적으로 지정한 경우
            if preferred_device in SUPPORTED_DEVICE_TYPES:
                print(f"🎯 사용자 지정 디바이스: {preferred_device}")
                return preferred_device
            else:
                print(f"⚠️ 지원하지 않는 디바이스: {preferred_device} (지원: {SUPPORTED_DEVICE_TYPES}), 자동 감지로 전환")
        
        print("🔍 최적 디바이스 자동 감지 중...")
        
        # CUDA 지원 확인
        try:
            import torch
            if torch.cuda.is_available():
                cuda_count = torch.cuda.device_count()
                current_device = torch.cuda.current_device()
                device_name = torch.cuda.get_device_name(current_device)
                memory_total = torch.cuda.get_device_properties(current_device).total_memory
                memory_gb = memory_total / (1024**3)
                
                self.device_info = {
                    "type": "cuda",
                    "count": cuda_count,
                    "current": current_device,
                    "name": device_name,
                    "memory_gb": round(memory_gb, 1),
                    "compute_capability": torch.cuda.get_device_capability(current_device)
                }
                
                print(f"✅ CUDA GPU 감지됨:")
                print(f"   - GPU 개수: {cuda_count}")
                print(f"   - 현재 GPU: {device_name}")
                print(f"   - VRAM: {memory_gb:.1f}GB")
                print(f"   - Compute Capability: {self.device_info['compute_capability']}")
                
                return "cuda"
                
        except ImportError:
            print("⚠️ PyTorch가 설치되지 않았습니다.")
        except Exception as e:
            print(f"⚠️ CUDA 확인 중 오류: {e}")
        
        # MPS (Apple Silicon) 지원 확인
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device_info = {
                    "type": "mps",
                    "platform": platform.platform(),
                    "processor": platform.processor()
                }
                
                print(f"✅ Apple MPS (Metal) 감지됨:")
                print(f"   - 플랫폼: {platform.platform()}")
                print(f"   - 프로세서: {platform.processor()}")
                
                return "mps"
                
        except ImportError:
            pass
        except Exception as e:
            print(f"⚠️ MPS 확인 중 오류: {e}")
        
        # CPU 폴백
        self.device_info = {
            "type": "cpu",
            "cores": os.cpu_count(),
            "platform": platform.platform(),
            "processor": platform.processor()
        }
        
        print(f"💻 CPU 사용:")
        print(f"   - 코어 수: {os.cpu_count()}")
        print(f"   - 플랫폼: {platform.platform()}")
        
        return "cpu"
    
    def _load_model(self):
        """모델을 로드하고 GPU 메모리 사용량을 최적화합니다."""
        try:
            print(f"🔄 BGE-M3 모델 로딩 중... (디바이스: {self.device})")
            start_time = time.time()
            
            # GPU 메모리 최적화 설정
            model_kwargs = {}
            if self.device == "cuda":
                # CUDA 최적화 설정
                model_kwargs.update({
                    "model_kwargs": {
                        "torch_dtype": "auto",  # 자동 precision 선택
                        "device_map": "auto",   # 자동 GPU 배치
                    }
                })
                
                # GPU 메모리 정리
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        print("🗑️ GPU 메모리 캐시 정리 완료")
                except:
                    pass
            
            self.model = SentenceTransformer(self.model_path, device=self.device, **model_kwargs)
            
            load_time = time.time() - start_time
            print(f"✅ BGE-M3 모델 로드 완료 ({load_time:.2f}초)")
            
            # 모델 정보 출력
            print(f"📊 모델 정보:")
            print(f"   - 모델명: {self.model_path}")
            print(f"   - 디바이스: {self.device}")
            print(f"   - 최대 시퀀스 길이: {self.model.max_seq_length}")
            
            # GPU 메모리 사용량 확인
            if self.device == "cuda":
                self._print_gpu_memory_usage()
            
        except Exception as e:
            print(f"❌ BGE-M3 모델 로드 실패: {e}")
            print("💡 해결 방법:")
            print("   1. sentence-transformers 설치: pip install sentence-transformers")
            print("   2. 네트워크 연결 확인 (모델 다운로드용)")
            print("   3. 디스크 공간 확인 (모델 크기: ~2GB)")
            if self.device == "cuda":
                print("   4. GPU 메모리 부족 시 CPU로 폴백: device='cpu'")
            raise
    
    def _print_gpu_memory_usage(self):
        """GPU 메모리 사용량을 출력합니다."""
        try:
            import torch
            if torch.cuda.is_available():
                current_device = torch.cuda.current_device()
                memory_allocated = torch.cuda.memory_allocated(current_device) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(current_device) / (1024**3)
                memory_total = torch.cuda.get_device_properties(current_device).total_memory / (1024**3)
                
                print(f"🔋 GPU 메모리 사용량:")
                print(f"   - 할당됨: {memory_allocated:.2f}GB")
                print(f"   - 예약됨: {memory_reserved:.2f}GB")
                print(f"   - 전체: {memory_total:.1f}GB")
                print(f"   - 사용률: {(memory_allocated/memory_total)*100:.1f}%")
                
        except Exception as e:
            print(f"⚠️ GPU 메모리 정보 확인 실패: {e}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서들을 임베딩합니다. (GPU 최적화)"""
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            print(f"🔄 {len(texts)}개 문서 임베딩 중...")
            start_time = time.time()
            
            # 디바이스별 배치 크기 최적화
            if self.device == "cuda":
                batch_size = 64  # GPU는 큰 배치 크기
                show_progress = len(texts) > 20
            elif self.device == "mps":
                batch_size = 32  # Apple Silicon 최적화
                show_progress = len(texts) > 15
            else:
                batch_size = 16  # CPU는 작은 배치 크기
                show_progress = len(texts) > 10
            
            # BGE-M3으로 임베딩 생성
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=False,
                show_progress_bar=show_progress,
                batch_size=batch_size,
                normalize_embeddings=True  # 코사인 유사도 최적화
            )
            
            embed_time = time.time() - start_time
            throughput = len(texts) / embed_time if embed_time > 0 else 0
            print(f"✅ 문서 임베딩 완료 ({embed_time:.2f}초, {throughput:.1f} docs/sec)")
            
            # GPU 메모리 정리 (대용량 처리 후)
            if self.device == "cuda" and len(texts) > 100:
                try:
                    import torch
                    torch.cuda.empty_cache()
                except:
                    pass
            
            # numpy array를 list로 변환
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            else:
                return [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
                
        except Exception as e:
            print(f"❌ 문서 임베딩 실패: {e}")
            if self.device == "cuda" and "out of memory" in str(e).lower():
                print("💡 GPU 메모리 부족 시 배치 크기를 줄이거나 CPU로 전환하세요.")
            # 실패한 경우 빈 벡터로 처리 (BGE-M3는 1024차원)
            return [[0.0] * 1024 for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """단일 쿼리를 임베딩합니다."""
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            print(f"🔄 쿼리 임베딩 중: {text[:50]}...")
            start_time = time.time()
            
            # BGE-M3으로 임베딩 생성
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            embed_time = time.time() - start_time
            print(f"✅ 쿼리 임베딩 완료 ({embed_time:.3f}초)")
            
            # numpy array를 list로 변환
            if hasattr(embedding, 'tolist'):
                return embedding.tolist()
            else:
                return embedding
                
        except Exception as e:
            print(f"❌ 쿼리 임베딩 실패: {e}")
            # 실패한 경우 빈 벡터로 처리 (BGE-M3는 1024차원)
            return [0.0] * 1024
    
    def similarity(self, embeddings1: List[List[float]], embeddings2: List[List[float]]) -> List[List[float]]:
        """임베딩 간 유사도를 계산합니다."""
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            import numpy as np
            
            # numpy array로 변환
            emb1 = np.array(embeddings1)
            emb2 = np.array(embeddings2)
            
            # 코사인 유사도 계산
            similarity_matrix = self.model.similarity(emb1, emb2)
            
            # numpy array를 list로 변환
            if hasattr(similarity_matrix, 'tolist'):
                return similarity_matrix.tolist()
            else:
                return similarity_matrix
                
        except Exception as e:
            print(f"❌ 유사도 계산 실패: {e}")
            # 실패한 경우 기본값 반환
            return [[0.0] * len(embeddings2) for _ in embeddings1]
    
    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """비동기 문서 임베딩 (동기 버전으로 폴백)"""
        return self.embed_documents(texts)
    
    async def aembed_query(self, text: str) -> List[float]:
        """비동기 쿼리 임베딩 (동기 버전으로 폴백)"""
        return self.embed_query(text)
    
    def save_model_locally(self, save_path: str):
        """모델을 로컬에 저장합니다."""
        if not self.model:
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        try:
            print(f"💾 BGE-M3 모델을 로컬에 저장 중: {save_path}")
            self.model.save(save_path)
            print(f"✅ 모델 저장 완료: {save_path}")
            
        except Exception as e:
            print(f"❌ 모델 저장 실패: {e}")
            raise
    
    def get_model_info(self) -> dict:
        """모델 정보를 반환합니다."""
        if not self.model:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_path": self.model_path,
            "device": self.device,
            "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown'),
            "embedding_dimension": 1024,  # BGE-M3 고정 차원
            "model_type": "BGE-M3",
            "device_info": self.device_info
        }
        
        # GPU 메모리 정보 추가
        if self.device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    current_device = torch.cuda.current_device()
                    memory_allocated = torch.cuda.memory_allocated(current_device) / (1024**3)
                    memory_total = torch.cuda.get_device_properties(current_device).total_memory / (1024**3)
                    
                    info["gpu_memory"] = {
                        "allocated_gb": round(memory_allocated, 2),
                        "total_gb": round(memory_total, 1),
                        "usage_percent": round((memory_allocated/memory_total)*100, 1)
                    }
            except:
                pass
        
        return info
    
    def get_device_capabilities(self) -> dict:
        """현재 디바이스의 성능 정보를 반환합니다."""
        capabilities = {
            "device": self.device,
            "auto_detected": True,
        }
        
        if self.device == "cuda":
            try:
                import torch
                if torch.cuda.is_available():
                    current_device = torch.cuda.current_device()
                    props = torch.cuda.get_device_properties(current_device)
                    
                    capabilities.update({
                        "gpu_name": props.name,
                        "compute_capability": f"{props.major}.{props.minor}",
                        "total_memory_gb": round(props.total_memory / (1024**3), 1),
                        "multiprocessor_count": props.multiprocessor_count,
                        "recommended_batch_size": 64,
                        "supports_mixed_precision": props.major >= 7,  # Volta 이상
                    })
            except:
                pass
                
        elif self.device == "mps":
            capabilities.update({
                "platform": platform.platform(),
                "recommended_batch_size": 32,
                "supports_mixed_precision": True,
            })
            
        else:  # CPU
            capabilities.update({
                "cpu_cores": os.cpu_count(),
                "platform": platform.platform(),
                "recommended_batch_size": 16,
                "supports_mixed_precision": False,
            })
        
        return capabilities