"""
Todo Continuation Logic for Sisyphus MCP.
Prevents stopping when tasks are incomplete.
"""

from sisyphus_mcp.state.manager import StateManager


def should_continue(state_manager: StateManager) -> bool:
    """
    작업 계속 여부 확인
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        True if should continue (incomplete tasks exist)
    """
    incomplete = state_manager.get_incomplete_todos()
    ultrawork = state_manager.get_ultrawork_state()
    ralph = state_manager.get_ralph_state()
    
    # 미완료 TODO가 있거나 Ultrawork/Ralph Loop 활성 시 계속
    if incomplete:
        return True
    if ultrawork and ultrawork.get("active"):
        return True
    if ralph and ralph.get("active"):
        return True
    
    return False


def get_continuation_message(state_manager: StateManager) -> str:
    """
    계속 진행 메시지 생성
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        계속 진행 안내 메시지
    """
    incomplete = state_manager.get_incomplete_todos()
    ultrawork = state_manager.get_ultrawork_state()
    ralph = state_manager.get_ralph_state()
    
    messages = []
    
    if incomplete:
        todo_list = "\n".join([f"  - [ ] {t.description}" for t in incomplete])
        messages.append(f"""
⚠️ **미완료 TODO가 있습니다!**

{todo_list}

모든 TODO를 완료한 후 종료해주세요.
""")
    
    if ultrawork and ultrawork.get("active"):
        iterations = ultrawork.get("iterations", 0)
        messages.append(f"""
🚀 **ULTRAWORK 모드 활성 중** (반복: {iterations}회)

Ultrawork 모드에서는 모든 작업이 완료될 때까지 계속해야 합니다.

## 체크리스트
- [ ] TODO LIST: 미완료 작업 제로
- [ ] FUNCTIONALITY: 모든 기능 동작
- [ ] TESTS: 테스트 통과
- [ ] ERRORS: 미해결 에러 제로
""")
    
    if ralph and ralph.get("active"):
        iteration = ralph.get("iteration", 0)
        max_iter = ralph.get("max_iterations", 10)
        promise = ralph.get("completion_promise", "TASK_COMPLETE")
        
        messages.append(f"""
🔄 **Ralph Loop 활성 중** (반복: {iteration}/{max_iter})

완료되면 다음을 출력하세요:
<promise>{promise}</promise>
""")
    
    if not messages:
        return ""
    
    return "\n---\n".join(messages)


def check_and_block_stop(state_manager: StateManager) -> dict:
    """
    Stop 시도 시 차단 여부 확인
    
    Args:
        state_manager: 상태 관리자
        
    Returns:
        {"should_block": bool, "message": str}
    """
    if should_continue(state_manager):
        return {
            "should_block": True,
            "message": get_continuation_message(state_manager)
        }
    
    return {
        "should_block": False,
        "message": "✅ 모든 작업이 완료되었습니다. 안전하게 종료할 수 있습니다."
    }
