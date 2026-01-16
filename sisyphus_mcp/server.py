"""
Sisyphus MCP Server for Antigravity IDE.
Provides multi-agent orchestration tools via Model Context Protocol.
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from sisyphus_mcp.state.manager import StateManager
from sisyphus_mcp.state.storage import Storage
from sisyphus_mcp.tools.definitions import TOOL_DEFINITIONS



# === DEBUG LOGGING ===
import os
import sys
import datetime
import traceback
from pathlib import Path

# 로그 파일 경로: ~/.gemini/sisyphus_server.log
LOG_FILE = Path.home() / ".gemini" / "sisyphus_server.log"

def log(msg: str):
    """디버그 로그 파일에 기록"""
    try:
        timestamp = datetime.datetime.now().isoformat()
        log_line = f"[{timestamp}] {msg}"
        
        # 파일 로깅
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except:
            pass
            
        # stderr로도 출력 (CLI 디버깅용)
        # 단, JSON-RPC 통신을 방해하지 않도록 주의 (stderr는 보통 안전함)
        print(log_line, file=sys.stderr)
        
    except:
        pass

def create_server(state_manager: StateManager | None = None) -> Server:
    """MCP 서버 인스턴스 생성"""
    log("Creating server instance...")
    server = Server("sisyphus-hooks")
    
    # 상태 관리자 초기화
    if state_manager is None:
        try:
            storage = Storage()
            state_manager = StateManager(storage)
            log("StateManager initialized")
        except Exception as e:
            log(f"Failed to init StateManager: {e}")
            raise
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """사용 가능한 도구 목록 반환"""
        log("list_tools called")
        tools = []
        
        for tool_name, tool_def in TOOL_DEFINITIONS.items():
            tools.append(Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                inputSchema=tool_def["parameters"]
            ))
        
        log(f"Returning {len(tools)} tools")
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """도구 실행"""
        log(f"call_tool: {name}")
        if name not in TOOL_DEFINITIONS:
            log(f"Unknown tool: {name}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"알 수 없는 도구: {name}"
                }, ensure_ascii=False)
            )]
        
        try:
            # 핸들러 호출
            handler = TOOL_DEFINITIONS[name]["handler"]
            result = handler(state_manager, **arguments)
            log(f"Tool {name} executed successfully")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
            log(f"Tool execution failed: {e}\n{traceback.format_exc()}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "error",
                    "message": f"도구 실행 실패: {str(e)}"
                }, ensure_ascii=False)
            )]
    
    return server


async def run_server_async():
    """비동기 서버 실행"""
    log(f"Async server starting. Python: {sys.executable}")
    log(f"Args: {sys.argv}")
    log(f"CWD: {os.getcwd()}")
    
    try:
        server = create_server()
        
        # 초기화 옵션 설정
        init_options = server.create_initialization_options()
        log("Initialization options created")
        
        async with stdio_server() as (read_stream, write_stream):
            log("Entering stdio_server loop")
            await server.run(
                read_stream,
                write_stream,
                init_options
            )
            log("Server loop finished usually")
    except Exception as e:
        log(f"Server error: {e}\n{traceback.format_exc()}")
        # 에러 로깅 (stderr로 출력하여 stdout 오염 방지)
        print(f"Server error: {e}", file=sys.stderr)
        raise


def run_server():
    """서버 실행 (동기 진입점)"""
    # 디렉토리 생성
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    except:
        pass
        
    log("=== SERVER STARTED ===")
    
    # msvcrt 설정 제거 (MCP SDK 1.25.0 호환성 테스트)
    # Windows에서 anyio와의 충돌 가능성 확인
    
    try:
        asyncio.run(run_server_async())
    except KeyboardInterrupt:
        log("KeyboardInterrupt")
    except Exception as e:
        log(f"Fatal error: {e}\n{traceback.format_exc()}")
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        log("=== SERVER STOPPED ===")


if __name__ == "__main__":
    run_server()
