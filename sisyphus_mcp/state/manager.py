"""
State Manager for Sisyphus MCP Server.
Centralized session state, TODO tracking, and ultrawork mode management.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
from pathlib import Path

from sisyphus_mcp.state.storage import Storage


class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class TodoItem:
    """TODO 항목"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    priority: int = 0  # 낮을수록 높은 우선순위
    
    def mark_complete(self) -> None:
        """완료 표시"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
    
    def mark_in_progress(self) -> None:
        """진행 중 표시"""
        self.status = TaskStatus.IN_PROGRESS


@dataclass
class SessionState:
    """세션 상태"""
    session_id: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    ultrawork_active: bool = False
    ultrawork_started_at: Optional[str] = None
    original_prompt: Optional[str] = None
    todos: list[dict] = field(default_factory=list)
    context: dict = field(default_factory=dict)


class StateManager:
    """
    세션 상태 관리자
    
    인프라 관점:
    - 단일 인스턴스로 모든 상태 관리
    - Storage를 통해 영속성 보장
    - 세션 간 컨텍스트 유지
    """
    
    # 저장소 키 상수
    KEY_SESSION = "session_state"
    KEY_TODOS = "todos"
    KEY_ULTRAWORK = "ultrawork_state"
    KEY_RALPH_LOOP = "ralph_loop"
    
    def __init__(self, storage: Optional[Storage] = None):
        self.storage = storage or Storage()
        self._session: Optional[SessionState] = None
    
    # === 세션 관리 ===
    
    def start_session(self, session_id: str, prompt: Optional[str] = None) -> SessionState:
        """
        새 세션 시작 또는 기존 세션 로드
        
        Args:
            session_id: 세션 식별자
            prompt: 초기 프롬프트
            
        Returns:
            세션 상태 객체
        """
        # 기존 세션 확인
        existing = self.storage.read(self.KEY_SESSION)
        
        if existing and existing.get("session_id") == session_id:
            # 기존 세션 재개
            self._session = SessionState(**existing)
            self._session.last_activity = datetime.now().isoformat()
        else:
            # 새 세션 생성
            self._session = SessionState(
                session_id=session_id,
                original_prompt=prompt
            )
        
        self._save_session()
        return self._session
    
    def get_session(self) -> Optional[SessionState]:
        """현재 세션 반환"""
        if self._session is None:
            data = self.storage.read(self.KEY_SESSION)
            if data:
                self._session = SessionState(**data)
        return self._session
    
    def update_activity(self) -> None:
        """마지막 활동 시간 갱신"""
        if self._session:
            self._session.last_activity = datetime.now().isoformat()
            self._save_session()
    
    def end_session(self) -> None:
        """세션 종료 (상태 정리)"""
        self.storage.delete(self.KEY_SESSION)
        self._session = None
    
    def _save_session(self) -> None:
        """세션 상태 저장"""
        if self._session:
            self.storage.write(self.KEY_SESSION, asdict(self._session))
    
    # === TODO 관리 ===
    
    def add_todo(self, description: str, priority: int = 0) -> TodoItem:
        """
        TODO 항목 추가
        
        Args:
            description: 작업 설명
            priority: 우선순위 (낮을수록 높음)
            
        Returns:
            생성된 TODO 항목
        """
        todos = self._load_todos()
        
        # ID 생성 (순차 증가)
        max_id = max([int(t.get("id", "0")) for t in todos], default=0)
        new_id = str(max_id + 1)
        
        todo = TodoItem(
            id=new_id,
            description=description,
            priority=priority
        )
        
        todos.append(asdict(todo))
        self.storage.write(self.KEY_TODOS, todos)
        
        return todo
    
    def get_todos(self, include_completed: bool = False) -> list[TodoItem]:
        """
        TODO 목록 조회
        
        Args:
            include_completed: 완료된 항목 포함 여부
            
        Returns:
            TODO 항목 목록 (우선순위 순)
        """
        todos = self._load_todos()
        
        items = [TodoItem(**t) for t in todos]
        
        if not include_completed:
            items = [t for t in items if t.status != TaskStatus.COMPLETED]
        
        # 우선순위 정렬 (낮은 값이 높은 우선순위)
        items.sort(key=lambda x: (x.priority, x.created_at))
        
        return items
    
    def get_incomplete_todos(self) -> list[TodoItem]:
        """미완료 TODO만 조회"""
        return [t for t in self.get_todos() if t.status != TaskStatus.COMPLETED]
    
    def mark_todo_complete(self, todo_id: str) -> bool:
        """TODO 완료 표시"""
        todos = self._load_todos()
        
        for todo in todos:
            if todo.get("id") == todo_id:
                todo["status"] = TaskStatus.COMPLETED.value
                todo["completed_at"] = datetime.now().isoformat()
                self.storage.write(self.KEY_TODOS, todos)
                return True
        
        return False
    
    def mark_todo_in_progress(self, todo_id: str) -> bool:
        """TODO 진행 중 표시"""
        todos = self._load_todos()
        
        for todo in todos:
            if todo.get("id") == todo_id:
                todo["status"] = TaskStatus.IN_PROGRESS.value
                self.storage.write(self.KEY_TODOS, todos)
                return True
        
        return False
    
    def clear_todos(self) -> None:
        """모든 TODO 삭제"""
        self.storage.delete(self.KEY_TODOS)
    
    def _load_todos(self) -> list[dict]:
        """TODO 목록 로드"""
        return self.storage.read(self.KEY_TODOS, default=[])
    
    # === Ultrawork 모드 ===
    
    def activate_ultrawork(self, prompt: str) -> dict:
        """
        Ultrawork 모드 활성화
        
        Args:
            prompt: 원본 프롬프트
            
        Returns:
            Ultrawork 상태
        """
        state = {
            "active": True,
            "started_at": datetime.now().isoformat(),
            "original_prompt": prompt,
            "iterations": 0
        }
        
        self.storage.write(self.KEY_ULTRAWORK, state)
        
        # 세션에도 반영
        if self._session:
            self._session.ultrawork_active = True
            self._session.ultrawork_started_at = state["started_at"]
            self._save_session()
        
        return state
    
    def get_ultrawork_state(self) -> Optional[dict]:
        """Ultrawork 상태 조회"""
        return self.storage.read(self.KEY_ULTRAWORK)
    
    def deactivate_ultrawork(self) -> None:
        """Ultrawork 모드 비활성화"""
        self.storage.delete(self.KEY_ULTRAWORK)
        
        if self._session:
            self._session.ultrawork_active = False
            self._session.ultrawork_started_at = None
            self._save_session()
    
    def increment_ultrawork_iteration(self) -> int:
        """Ultrawork 반복 횟수 증가"""
        state = self.get_ultrawork_state()
        
        if state and state.get("active"):
            state["iterations"] = state.get("iterations", 0) + 1
            self.storage.write(self.KEY_ULTRAWORK, state)
            return state["iterations"]
        
        return 0
    
    # === Ralph Loop ===
    
    def start_ralph_loop(self, prompt: str, completion_promise: str, max_iterations: int = 10) -> dict:
        """
        Ralph Loop 시작
        
        Args:
            prompt: 작업 프롬프트
            completion_promise: 완료 시 출력할 문자열
            max_iterations: 최대 반복 횟수
            
        Returns:
            Ralph Loop 상태
        """
        state = {
            "active": True,
            "prompt": prompt,
            "completion_promise": completion_promise,
            "max_iterations": max_iterations,
            "iteration": 0,
            "started_at": datetime.now().isoformat()
        }
        
        self.storage.write(self.KEY_RALPH_LOOP, state)
        return state
    
    def get_ralph_state(self) -> Optional[dict]:
        """Ralph Loop 상태 조회"""
        return self.storage.read(self.KEY_RALPH_LOOP)
    
    def increment_ralph_iteration(self) -> Optional[dict]:
        """Ralph Loop 반복 증가"""
        state = self.get_ralph_state()
        
        if state and state.get("active"):
            state["iteration"] = state.get("iteration", 0) + 1
            self.storage.write(self.KEY_RALPH_LOOP, state)
            return state
        
        return None
    
    def end_ralph_loop(self) -> None:
        """Ralph Loop 종료"""
        self.storage.delete(self.KEY_RALPH_LOOP)
    
    # === 컨텍스트 관리 ===
    
    def set_context(self, key: str, value: any) -> None:
        """세션 컨텍스트에 값 저장"""
        if self._session:
            self._session.context[key] = value
            self._save_session()
    
    def get_context(self, key: str, default: any = None) -> any:
        """세션 컨텍스트에서 값 조회"""
        if self._session:
            return self._session.context.get(key, default)
        return default
    
    # === 검증 ===
    
    def verify_completion(self) -> dict:
        """
        완료 상태 검증
        
        Returns:
            검증 결과 딕셔너리
        """
        incomplete_todos = self.get_incomplete_todos()
        ultrawork = self.get_ultrawork_state()
        ralph = self.get_ralph_state()
        
        can_stop = len(incomplete_todos) == 0
        
        blockers = []
        if incomplete_todos:
            blockers.append(f"미완료 TODO {len(incomplete_todos)}개")
        if ultrawork and ultrawork.get("active"):
            blockers.append("Ultrawork 모드 활성 중")
        if ralph and ralph.get("active"):
            blockers.append("Ralph Loop 활성 중")
        
        return {
            "can_stop": can_stop and not blockers,
            "incomplete_todo_count": len(incomplete_todos),
            "incomplete_todos": [asdict(t) for t in incomplete_todos],
            "ultrawork_active": bool(ultrawork and ultrawork.get("active")),
            "ralph_active": bool(ralph and ralph.get("active")),
            "blockers": blockers,
            "message": "완료 가능" if not blockers else f"중단 불가: {', '.join(blockers)}"
        }
