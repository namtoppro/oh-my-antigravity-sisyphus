"""
Storage module for persistent state management.
Handles JSON file-based storage with backup and recovery capabilities.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# 기본 저장소 경로
DEFAULT_GEMINI_DIR = Path.home() / ".gemini"
DEFAULT_SISYPHUS_DIR = DEFAULT_GEMINI_DIR / ".sisyphus"
DEFAULT_BACKUP_DIR = DEFAULT_SISYPHUS_DIR / "backups"


def get_default_storage_path() -> Path:
    """기본 저장소 경로 반환"""
    return DEFAULT_SISYPHUS_DIR


def get_backup_dir() -> Path:
    """백업 디렉토리 경로 반환"""
    return DEFAULT_BACKUP_DIR


class Storage:
    """
    JSON 기반 영속 저장소
    
    인프라 관점:
    - 파일 락 없이 단일 프로세스 가정 (MCP 서버는 단일 인스턴스)
    - 원자적 쓰기를 위해 임시 파일 후 rename 사용
    - 자동 백업 기능으로 데이터 손실 방지
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or get_default_storage_path()
        self.backup_dir = self.base_dir / "backups"
        self._ensure_dirs()
    
    def _ensure_dirs(self) -> None:
        """필요한 디렉토리 생성"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """키에 해당하는 파일 경로 반환"""
        # 키에서 안전한 파일명 생성
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe_key}.json"
    
    def read(self, key: str, default: Any = None) -> Any:
        """
        키에 해당하는 데이터 읽기
        
        Args:
            key: 데이터 키 (예: "session_state", "todos")
            default: 파일이 없거나 읽기 실패 시 반환값
            
        Returns:
            저장된 데이터 또는 default 값
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # 손상된 파일 로깅 및 default 반환
            print(f"[Storage] 읽기 실패 ({key}): {e}")
            return default
    
    def write(self, key: str, data: Any) -> bool:
        """
        데이터 저장 (원자적 쓰기)
        
        Args:
            key: 데이터 키
            data: 저장할 데이터 (JSON 직렬화 가능)
            
        Returns:
            성공 여부
        """
        file_path = self._get_file_path(key)
        temp_path = file_path.with_suffix(".tmp")
        
        try:
            # 1. 임시 파일에 쓰기
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # 2. 원자적 rename
            temp_path.replace(file_path)
            return True
            
        except (IOError, TypeError) as e:
            print(f"[Storage] 쓰기 실패 ({key}): {e}")
            # 임시 파일 정리
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def delete(self, key: str) -> bool:
        """키에 해당하는 데이터 삭제"""
        file_path = self._get_file_path(key)
        
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except IOError as e:
                print(f"[Storage] 삭제 실패 ({key}): {e}")
                return False
        return True  # 이미 없으면 성공으로 처리
    
    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        return self._get_file_path(key).exists()
    
    def list_keys(self) -> list[str]:
        """모든 키 목록 반환"""
        keys = []
        for file_path in self.base_dir.glob("*.json"):
            keys.append(file_path.stem)
        return sorted(keys)
    
    # === 백업/복구 기능 ===
    
    def create_backup(self, backup_id: Optional[str] = None) -> str:
        """
        현재 상태 전체 백업 생성
        
        Args:
            backup_id: 백업 식별자 (미지정 시 타임스탬프 사용)
            
        Returns:
            생성된 백업 ID
        """
        if backup_id is None:
            backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 모든 JSON 파일 복사
        for json_file in self.base_dir.glob("*.json"):
            shutil.copy2(json_file, backup_path / json_file.name)
        
        # 백업 메타데이터 저장
        meta = {
            "backup_id": backup_id,
            "created_at": datetime.now().isoformat(),
            "files": [f.name for f in backup_path.glob("*.json")]
        }
        with open(backup_path / "_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        return backup_id
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        백업에서 상태 복구
        
        Args:
            backup_id: 복구할 백업 ID
            
        Returns:
            성공 여부
        """
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            print(f"[Storage] 백업 없음: {backup_id}")
            return False
        
        try:
            # 현재 상태 자동 백업 (복구 전 안전장치)
            self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # 백업 파일들 복원
            for json_file in backup_path.glob("*.json"):
                if json_file.name != "_meta.json":
                    shutil.copy2(json_file, self.base_dir / json_file.name)
            
            return True
            
        except IOError as e:
            print(f"[Storage] 복구 실패: {e}")
            return False
    
    def list_backups(self) -> list[dict]:
        """
        백업 목록 조회
        
        Returns:
            백업 메타데이터 목록 (최신순 정렬)
        """
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if backup_dir.is_dir():
                meta_file = backup_dir / "_meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            backups.append(meta)
                    except (json.JSONDecodeError, IOError):
                        # 메타 파일 손상 시 기본 정보
                        backups.append({
                            "backup_id": backup_dir.name,
                            "created_at": "unknown",
                            "files": []
                        })
        
        # 생성일 기준 최신순 정렬
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """백업 삭제"""
        backup_path = self.backup_dir / backup_id
        
        if backup_path.exists():
            try:
                shutil.rmtree(backup_path)
                return True
            except IOError as e:
                print(f"[Storage] 백업 삭제 실패: {e}")
                return False
        return True
