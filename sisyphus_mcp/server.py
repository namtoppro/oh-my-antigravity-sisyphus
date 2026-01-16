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


def create_server(state_manager: StateManager | None = None) -> Server:
    """
    MCP 서버 인스턴스 생성
    
    Args:
        state_manager: 상태 관리자 (미지정 시 기본 생성)
        
    Returns:
        MCP Server 인스턴스
    """
    server = Server("sisyphus-hooks")
    
    # 상태 관리자 초기화
    if state_manager is None:
        storage = Storage()
        state_manager = StateManager(storage)
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """사용 가능한 도구 목록 반환"""
        tools = []
        
        for tool_name, tool_def in TOOL_DEFINITIONS.items():
            tools.append(Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                inputSchema=tool_def["parameters"]
            ))
        
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        도구 실행
        
        Args:
            name: 도구 이름
            arguments: 도구 인자
            
        Returns:
            실행 결과
        """
        if name not in TOOL_DEFINITIONS:
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
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2)
            )]
            
        except Exception as e:
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
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run_server():
    """서버 실행 (동기 진입점)"""
    asyncio.run(run_server_async())


if __name__ == "__main__":
    run_server()
