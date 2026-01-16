"""
MCP Tool Definitions for Sisyphus.
Each tool is a callable that operates on the StateManager.
"""

from typing import Any, Callable
from sisyphus_mcp.state.manager import StateManager


def sisyphus_start_task(state_manager: StateManager, task_description: str, session_id: str = "default") -> dict:
    """
    새 작업 시작 및 상태 초기화
    
    Args:
        state_manager: 상태 관리자
        task_description: 작업 설명
        session_id: 세션 식별자
        
    Returns:
        시작된 작업 정보
    """
    # 세션 시작
    session = state_manager.start_session(session_id, task_description)
    
    # 기존 TODO 정리 (선택적)
    # state_manager.clear_todos()
    
    # 메인 작업을 TODO로 추가
    todo = state_manager.add_todo(task_description, priority=0)
    
    return {
        "status": "success",
        "message": f"작업이 시작되었습니다: {task_description}",
        "session_id": session.session_id,
        "todo_id": todo.id,
        "started_at": session.started_at
    }


def sisyphus_check_todos(state_manager: StateManager, include_completed: bool = False) -> dict:
    """
    미완료 TODO 목록 확인
    
    Args:
        state_manager: 상태 관리자
        include_completed: 완료된 항목 포함 여부
        
    Returns:
        TODO 목록 및 상태
    """
    todos = state_manager.get_todos(include_completed=include_completed)
    incomplete = [t for t in todos if t.status.value != "completed"]
    
    return {
        "status": "success",
        "total_count": len(todos),
        "incomplete_count": len(incomplete),
        "todos": [
            {
                "id": t.id,
                "description": t.description,
                "status": t.status.value,
                "priority": t.priority,
                "created_at": t.created_at
            }
            for t in todos
        ],
        "can_stop": len(incomplete) == 0,
        "message": f"미완료 TODO {len(incomplete)}개" if incomplete else "모든 TODO 완료!"
    }


def sisyphus_add_todo(state_manager: StateManager, description: str, priority: int = 0) -> dict:
    """
    새 TODO 항목 추가
    
    Args:
        state_manager: 상태 관리자
        description: 작업 설명
        priority: 우선순위 (낮을수록 높음)
        
    Returns:
        추가된 TODO 정보
    """
    todo = state_manager.add_todo(description, priority)
    
    return {
        "status": "success",
        "message": f"TODO 추가됨: {description}",
        "todo": {
            "id": todo.id,
            "description": todo.description,
            "status": todo.status.value,
            "priority": todo.priority
        }
    }


def sisyphus_complete_todo(state_manager: StateManager, todo_id: str) -> dict:
    """
    TODO 완료 표시
    
    Args:
        state_manager: 상태 관리자
        todo_id: TODO ID
        
    Returns:
        완료 결과
    """
    success = state_manager.mark_todo_complete(todo_id)
    
    if success:
        remaining = len(state_manager.get_incomplete_todos())
        return {
            "status": "success",
            "message": f"TODO {todo_id} 완료됨",
            "remaining_count": remaining,
            "can_stop": remaining == 0
        }
    else:
        return {
            "status": "error",
            "message": f"TODO {todo_id}를 찾을 수 없습니다"
        }


def sisyphus_verify_completion(state_manager: StateManager) -> dict:
    """
    완료 상태 검증 - 중단 전 필수 호출
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        검증 결과
    """
    result = state_manager.verify_completion()
    
    if result["can_stop"]:
        return {
            "status": "success",
            "can_stop": True,
            "message": "✅ 모든 작업이 완료되었습니다. 안전하게 종료할 수 있습니다."
        }
    else:
        blockers_str = "\n".join([f"  - {b}" for b in result["blockers"]])
        return {
            "status": "blocked",
            "can_stop": False,
            "blockers": result["blockers"],
            "incomplete_todos": result["incomplete_todos"],
            "message": f"⚠️ 다음 항목이 완료되지 않았습니다:\n{blockers_str}\n\n계속 작업해주세요!"
        }


def sisyphus_activate_ultrawork(state_manager: StateManager, prompt: str) -> dict:
    """
    Ultrawork 모드 활성화
    
    Args:
        state_manager: 상태 관리자
        prompt: 원본 프롬프트
        
    Returns:
        Ultrawork 상태
    """
    state = state_manager.activate_ultrawork(prompt)
    
    return {
        "status": "success",
        "message": "🚀 ULTRAWORK 모드 활성화!",
        "ultrawork_state": state,
        "instructions": """
ULTRAWORK 모드가 활성화되었습니다.

## 행동 규칙
1. **병렬 작업 우선** - 독립적인 작업은 동시에 실행
2. **적극적 위임** - 복잡한 작업은 분해
3. **검증 필수** - 중단 전 sisyphus_verify_completion 호출

## 중단 전 체크리스트
- [ ] TODO LIST: 미완료 작업 제로
- [ ] FUNCTIONALITY: 모든 기능 동작
- [ ] TESTS: 테스트 통과
- [ ] ERRORS: 미해결 에러 제로
"""
    }


def sisyphus_deactivate_ultrawork(state_manager: StateManager) -> dict:
    """
    Ultrawork 모드 비활성화
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        결과
    """
    state_manager.deactivate_ultrawork()
    
    return {
        "status": "success",
        "message": "Ultrawork 모드가 비활성화되었습니다."
    }


def sisyphus_get_context(state_manager: StateManager) -> dict:
    """
    세션 컨텍스트 로드
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        세션 컨텍스트
    """
    session = state_manager.get_session()
    todos = state_manager.get_incomplete_todos()
    ultrawork = state_manager.get_ultrawork_state()
    ralph = state_manager.get_ralph_state()
    
    context = {
        "status": "success",
        "session": None,
        "incomplete_todos": [],
        "ultrawork_active": False,
        "ralph_active": False
    }
    
    if session:
        context["session"] = {
            "session_id": session.session_id,
            "started_at": session.started_at,
            "last_activity": session.last_activity,
            "original_prompt": session.original_prompt
        }
    
    if todos:
        context["incomplete_todos"] = [
            {"id": t.id, "description": t.description, "status": t.status.value}
            for t in todos
        ]
    
    if ultrawork and ultrawork.get("active"):
        context["ultrawork_active"] = True
        context["ultrawork"] = ultrawork
    
    if ralph and ralph.get("active"):
        context["ralph_active"] = True
        context["ralph"] = ralph
    
    # 복원 메시지 생성
    messages = []
    if context["incomplete_todos"]:
        messages.append(f"미완료 TODO {len(context['incomplete_todos'])}개 있음")
    if context["ultrawork_active"]:
        messages.append("Ultrawork 모드 활성 중")
    if context["ralph_active"]:
        messages.append("Ralph Loop 활성 중")
    
    context["message"] = ", ".join(messages) if messages else "새 세션"
    
    return context


def sisyphus_start_ralph_loop(
    state_manager: StateManager, 
    prompt: str, 
    completion_promise: str = "TASK_COMPLETE",
    max_iterations: int = 10
) -> dict:
    """
    Ralph Loop 시작 - 완료까지 자동 반복
    
    Args:
        state_manager: 상태 관리자
        prompt: 작업 프롬프트
        completion_promise: 완료 시 출력할 문자열
        max_iterations: 최대 반복 횟수
        
    Returns:
        Ralph Loop 상태
    """
    state = state_manager.start_ralph_loop(prompt, completion_promise, max_iterations)
    
    return {
        "status": "success",
        "message": f"🔄 Ralph Loop 시작 (최대 {max_iterations}회 반복)",
        "ralph_state": state,
        "instructions": f"""
Ralph Loop가 시작되었습니다.

작업 완료 시 다음 문자열을 출력하세요:
<promise>{completion_promise}</promise>

이 문자열이 출력되면 Ralph Loop가 종료됩니다.
최대 {max_iterations}회 반복 후 자동 종료됩니다.
"""
    }


def sisyphus_end_ralph_loop(state_manager: StateManager) -> dict:
    """
    Ralph Loop 종료
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        결과
    """
    state_manager.end_ralph_loop()
    
    return {
        "status": "success",
        "message": "Ralph Loop가 종료되었습니다."
    }


# 도구 정의 메타데이터
TOOL_DEFINITIONS = {
    "sisyphus_start_task": {
        "name": "sisyphus_start_task",
        "description": "새 작업 시작 및 상태 초기화. 작업 시작 시 호출하세요.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "작업 설명"
                },
                "session_id": {
                    "type": "string",
                    "description": "세션 식별자 (기본값: default)",
                    "default": "default"
                }
            },
            "required": ["task_description"]
        },
        "handler": sisyphus_start_task
    },
    "sisyphus_check_todos": {
        "name": "sisyphus_check_todos",
        "description": "미완료 TODO 목록 확인. 작업 중단 전 반드시 호출하세요.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_completed": {
                    "type": "boolean",
                    "description": "완료된 항목 포함 여부",
                    "default": False
                }
            }
        },
        "handler": sisyphus_check_todos
    },
    "sisyphus_add_todo": {
        "name": "sisyphus_add_todo",
        "description": "새 TODO 항목 추가.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "TODO 설명"
                },
                "priority": {
                    "type": "integer",
                    "description": "우선순위 (낮을수록 높음)",
                    "default": 0
                }
            },
            "required": ["description"]
        },
        "handler": sisyphus_add_todo
    },
    "sisyphus_complete_todo": {
        "name": "sisyphus_complete_todo",
        "description": "TODO 항목 완료 표시.",
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "string",
                    "description": "완료할 TODO ID"
                }
            },
            "required": ["todo_id"]
        },
        "handler": sisyphus_complete_todo
    },
    "sisyphus_verify_completion": {
        "name": "sisyphus_verify_completion",
        "description": "완료 상태 검증. 작업 종료 전 필수 호출!",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": sisyphus_verify_completion
    },
    "sisyphus_activate_ultrawork": {
        "name": "sisyphus_activate_ultrawork",
        "description": "Ultrawork 모드 활성화. 최대 성능 모드로 전환.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "원본 프롬프트"
                }
            },
            "required": ["prompt"]
        },
        "handler": sisyphus_activate_ultrawork
    },
    "sisyphus_deactivate_ultrawork": {
        "name": "sisyphus_deactivate_ultrawork",
        "description": "Ultrawork 모드 비활성화.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": sisyphus_deactivate_ultrawork
    },
    "sisyphus_get_context": {
        "name": "sisyphus_get_context",
        "description": "세션 컨텍스트 로드. 세션 복원 시 호출.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": sisyphus_get_context
    },
    "sisyphus_start_ralph_loop": {
        "name": "sisyphus_start_ralph_loop",
        "description": "Ralph Loop 시작. 완료까지 자동 반복.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "작업 프롬프트"
                },
                "completion_promise": {
                    "type": "string",
                    "description": "완료 시 출력할 문자열",
                    "default": "TASK_COMPLETE"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "최대 반복 횟수",
                    "default": 10
                }
            },
            "required": ["prompt"]
        },
        "handler": sisyphus_start_ralph_loop
    },
    "sisyphus_end_ralph_loop": {
        "name": "sisyphus_end_ralph_loop",
        "description": "Ralph Loop 종료.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": sisyphus_end_ralph_loop
    }
}


def get_tool_handler(tool_name: str) -> Callable:
    """도구 핸들러 함수 반환"""
    if tool_name in TOOL_DEFINITIONS:
        return TOOL_DEFINITIONS[tool_name]["handler"]
    raise ValueError(f"Unknown tool: {tool_name}")
