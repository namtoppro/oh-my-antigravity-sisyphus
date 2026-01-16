"""
Sisyphus MCP CLI - 설치/백업/복구/상태 관리 도구

Usage:
    sisyphus-mcp install     # 설치 (자동 백업 포함)
    sisyphus-mcp uninstall   # 제거
    sisyphus-mcp backup      # 백업 생성
    sisyphus-mcp restore     # 백업에서 복구
    sisyphus-mcp status      # 상태 확인
    sisyphus-mcp doctor      # 연결 진단
    sisyphus-mcp list-backups # 백업 목록
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from sisyphus_mcp.state.storage import Storage, DEFAULT_GEMINI_DIR, DEFAULT_SISYPHUS_DIR

console = Console()

# 설정 경로
GEMINI_MD_PATH = DEFAULT_GEMINI_DIR / "GEMINI.md"
MCP_CONFIG_PATH = DEFAULT_GEMINI_DIR / "antigravity" / "mcp_config.json"
BACKUP_DIR = DEFAULT_SISYPHUS_DIR / "backups"

# 내장 GEMINI.md 템플릿 (패키지에서 로드하거나 기본값 사용)
GEMINI_MD_TEMPLATE_URL = "https://raw.githubusercontent.com/your-repo/oh-my-antigravity-sisyphus/main/templates/GEMINI.md"


def get_template_path() -> Optional[Path]:
    """템플릿 파일 경로 반환 (pip 설치 대응)"""
    import sys
    
    # 방법 1: 패키지 내부 경로 (pip 설치)
    try:
        import sisyphus_mcp
        package_dir = Path(sisyphus_mcp.__file__).parent
        template_path = package_dir / "templates" / "GEMINI.md"
        if template_path.exists():
            return template_path
    except:
        pass
    
    # 방법 2: 개발 환경 (소스 설치)
    dev_path = Path(__file__).parent.parent / "templates" / "GEMINI.md"
    if dev_path.exists():
        return dev_path
    
    # 방법 3: 상위 디렉토리 탐색
    for parent in Path(__file__).parents:
        template_path = parent / "templates" / "GEMINI.md"
        if template_path.exists():
            return template_path
        template_path = parent / "sisyphus_mcp" / "templates" / "GEMINI.md"
        if template_path.exists():
            return template_path
    
    return None


@click.group()
@click.version_option(version="1.0.0", prog_name="sisyphus-mcp")
def cli():
    """🪨 Oh-My-Antigravity-Sisyphus MCP 관리 도구"""
    pass


@cli.command()
@click.option("--force", "-f", is_flag=True, help="기존 설정 덮어쓰기")
@click.option("--no-backup", is_flag=True, help="자동 백업 건너뛰기")
def install(force: bool, no_backup: bool):
    """
    Sisyphus MCP 서버 설치
    
    1. 기존 설정 자동 백업
    2. GEMINI.md 설정 (시스템 프롬프트)
    3. mcp_config.json 설정 (MCP 서버 등록)
    4. 상태 저장소 초기화
    """
    console.print(Panel.fit(
        "[bold cyan]🪨 Oh-My-Antigravity-Sisyphus 설치[/bold cyan]\n"
        "시시포스처럼, 작업이 완료될 때까지 멈추지 않습니다.",
        border_style="cyan"
    ))
    
    # 1. 자동 백업
    if not no_backup:
        console.print("\n[yellow]📦 기존 설정 백업 중...[/yellow]")
        backup_id = _create_full_backup()
        if backup_id:
            console.print(f"[green]✓ 백업 완료: {backup_id}[/green]")
        else:
            console.print("[dim]백업할 기존 설정 없음[/dim]")
    
    # 2. 디렉토리 생성
    console.print("\n[yellow]📁 디렉토리 생성 중...[/yellow]")
    _ensure_directories()
    console.print("[green]✓ 디렉토리 준비 완료[/green]")
    
    # 3. GEMINI.md 설치
    console.print("\n[yellow]📝 GEMINI.md 설정 중...[/yellow]")
    gemini_result = _install_gemini_md(force)
    if gemini_result["success"]:
        console.print(f"[green]✓ {gemini_result['message']}[/green]")
    else:
        console.print(f"[red]✗ {gemini_result['message']}[/red]")
        if not force:
            console.print("[dim]--force 옵션으로 덮어쓰기 가능[/dim]")
    
    # 4. MCP 설정
    console.print("\n[yellow]⚙️ MCP 서버 등록 중...[/yellow]")
    mcp_result = _install_mcp_config(force)
    if mcp_result["success"]:
        console.print(f"[green]✓ {mcp_result['message']}[/green]")
    else:
        console.print(f"[yellow]⚠ {mcp_result['message']}[/yellow]")
    
    # 5. 상태 저장소 초기화
    console.print("\n[yellow]💾 상태 저장소 초기화 중...[/yellow]")
    storage = Storage()
    console.print(f"[green]✓ 저장소 준비 완료: {storage.base_dir}[/green]")
    
    # 완료 메시지
    console.print(Panel.fit(
        "[bold green]✅ 설치 완료![/bold green]\n\n"
        "Antigravity IDE를 재시작하면 MCP 도구가 활성화됩니다.\n\n"
        "[dim]사용 가능한 도구:[/dim]\n"
        "• sisyphus_start_task - 작업 시작\n"
        "• sisyphus_check_todos - TODO 확인\n"
        "• sisyphus_verify_completion - 완료 검증\n"
        "• sisyphus_activate_ultrawork - Ultrawork 모드",
        border_style="green"
    ))


@cli.command()
@click.option("--keep-backups", is_flag=True, help="백업 유지")
@click.confirmation_option(prompt="설정을 제거하시겠습니까?")
def uninstall(keep_backups: bool):
    """
    Sisyphus MCP 서버 제거
    
    - MCP 설정에서 sisyphus-hooks 제거
    - 상태 저장소 삭제 (선택적)
    - GEMINI.md는 유지 (수동 복구 필요)
    """
    console.print("[yellow]🗑️ Sisyphus MCP 제거 중...[/yellow]")
    
    # 1. MCP 설정에서 제거
    if MCP_CONFIG_PATH.exists():
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            if "mcpServers" in config and "sisyphus-hooks" in config["mcpServers"]:
                del config["mcpServers"]["sisyphus-hooks"]
                
                with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                console.print("[green]✓ MCP 설정에서 제거됨[/green]")
        except Exception as e:
            console.print(f"[red]✗ MCP 설정 수정 실패: {e}[/red]")
    
    # 2. 상태 저장소 삭제
    if DEFAULT_SISYPHUS_DIR.exists():
        if keep_backups:
            # 백업만 유지하고 나머지 삭제
            for item in DEFAULT_SISYPHUS_DIR.iterdir():
                if item.name != "backups":
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)
            console.print("[green]✓ 상태 저장소 정리 (백업 유지)[/green]")
        else:
            shutil.rmtree(DEFAULT_SISYPHUS_DIR)
            console.print("[green]✓ 상태 저장소 삭제됨[/green]")
    
    console.print(Panel.fit(
        "[bold yellow]제거 완료[/bold yellow]\n\n"
        "GEMINI.md는 유지됩니다.\n"
        "복구하려면: sisyphus-mcp restore [backup_id]",
        border_style="yellow"
    ))


@cli.command()
@click.option("--id", "backup_id", help="백업 ID (기본: 타임스탬프)")
def backup(backup_id: Optional[str]):
    """현재 설정 백업 생성"""
    console.print("[yellow]📦 백업 생성 중...[/yellow]")
    
    result_id = _create_full_backup(backup_id)
    
    if result_id:
        console.print(f"[green]✓ 백업 완료: {result_id}[/green]")
        console.print(f"[dim]위치: {BACKUP_DIR / result_id}[/dim]")
    else:
        console.print("[red]✗ 백업 실패[/red]")


@cli.command()
@click.argument("backup_id", required=False)
@click.option("--list", "list_only", is_flag=True, help="백업 목록만 표시")
def restore(backup_id: Optional[str], list_only: bool):
    """백업에서 설정 복구"""
    storage = Storage()
    backups = storage.list_backups()
    
    if list_only or not backup_id:
        # 백업 목록 표시
        if not backups:
            console.print("[yellow]사용 가능한 백업이 없습니다.[/yellow]")
            return
        
        table = Table(title="📦 백업 목록")
        table.add_column("ID", style="cyan")
        table.add_column("생성일", style="green")
        table.add_column("파일 수", justify="right")
        
        for b in backups:
            table.add_row(
                b["backup_id"],
                b.get("created_at", "unknown")[:19],
                str(len(b.get("files", [])))
            )
        
        console.print(table)
        
        if not backup_id:
            console.print("\n[dim]복구하려면: sisyphus-mcp restore [BACKUP_ID][/dim]")
            return
    
    # 복구 실행
    console.print(f"[yellow]🔄 백업 복구 중: {backup_id}[/yellow]")
    
    if storage.restore_backup(backup_id):
        console.print("[green]✓ 복구 완료[/green]")
    else:
        console.print("[red]✗ 복구 실패[/red]")


@cli.command("list-backups")
def list_backups():
    """백업 목록 조회"""
    storage = Storage()
    backups = storage.list_backups()
    
    if not backups:
        console.print("[yellow]사용 가능한 백업이 없습니다.[/yellow]")
        return
    
    table = Table(title="📦 백업 목록")
    table.add_column("ID", style="cyan")
    table.add_column("생성일", style="green")
    table.add_column("파일 수", justify="right")
    
    for b in backups:
        table.add_row(
            b["backup_id"],
            b.get("created_at", "unknown")[:19],
            str(len(b.get("files", [])))
        )
    
    console.print(table)


@cli.command()
def status():
    """설치 상태 확인"""
    console.print(Panel.fit(
        "[bold cyan]🪨 Sisyphus MCP 상태[/bold cyan]",
        border_style="cyan"
    ))
    
    checks = []
    
    # GEMINI.md 확인
    if GEMINI_MD_PATH.exists():
        with open(GEMINI_MD_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "Oh-My-Antigravity-Sisyphus" in content:
            checks.append(("GEMINI.md", "✅ 설치됨", "green"))
        else:
            checks.append(("GEMINI.md", "⚠️ 존재하지만 Sisyphus 설정 없음", "yellow"))
    else:
        checks.append(("GEMINI.md", "❌ 없음", "red"))
    
    # MCP 설정 확인
    if MCP_CONFIG_PATH.exists():
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            if config.get("mcpServers", {}).get("sisyphus-hooks"):
                checks.append(("MCP 설정", "✅ 등록됨", "green"))
            else:
                checks.append(("MCP 설정", "⚠️ 파일 존재, 서버 미등록", "yellow"))
        except:
            checks.append(("MCP 설정", "⚠️ 파일 손상", "yellow"))
    else:
        checks.append(("MCP 설정", "❌ 없음", "red"))
    
    # 경로 정보
    console.print("\n[dim]경로:[/dim]")
    console.print(f"  GEMINI.md: {GEMINI_MD_PATH}")
    console.print(f"  MCP 설정: {MCP_CONFIG_PATH}")
    console.print(f"  저장소: {DEFAULT_SISYPHUS_DIR}")


@cli.command()
def doctor():
    """MCP 서버 연결 상태 진단"""
    import subprocess
    import os
    import sys
    import time
    import threading
    
    console.print(Panel.fit(
        "[bold cyan]🩺 Sisyphus MCP 진단 도구[/bold cyan]",
        border_style="cyan"
    ))
    
    # 1. 설정 파일 확인
    console.print("\n[yellow]1. 설정 파일 확인[/yellow]")
    if not MCP_CONFIG_PATH.exists():
        console.print(f"[red]✗ 설정 파일 없음: {MCP_CONFIG_PATH}[/red]")
        return
        
    try:
        with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        console.print("[green]✓ 설정 파일 로드 성공[/green]")
    except Exception as e:
        console.print(f"[red]✗ 설정 파일 파싱 실패: {e}[/red]")
        return
        
    # 2. 서버 설정 확인
    console.print("\n[yellow]2. 서버 설정 확인[/yellow]")
    sisyphus_conf = config.get("mcpServers", {}).get("sisyphus-hooks")
    
    if not sisyphus_conf:
        console.print("[red]✗ sisyphus-hooks 설정 없음[/red]")
        return
        
    cmd = sisyphus_conf.get("command")
    args = sisyphus_conf.get("args", [])
    env_vars = sisyphus_conf.get("env", {})
    
    console.print(f"  Command: {cmd}")
    console.print(f"  Args: {args}")
    
    if not Path(cmd).exists():
        console.print(f"[red]✗ 실행 파일을 찾을 수 없음: {cmd}[/red]")
    else:
        console.print("[green]✓ 실행 파일 확인됨[/green]")
        
    # 3. 서버 프로세스 테스트
    console.print("\n[yellow]3. 서버 통신 테스트 (JSON-RPC initialize)[/yellow]")
    
    proc_env = os.environ.copy()
    proc_env.update(env_vars)
    full_cmd = [cmd] + args
    
    try:
        process = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=proc_env,
            # Windows 바이너리 모드 처리 (중요)
            text=False
        )
        console.print("[green]✓ 프로세스 시작됨[/green]")
    except Exception as e:
        console.print(f"[red]✗ 프로세스 실행 실패: {e}[/red]")
        return

    # Initialize 요청
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "sisyphus-doctor", "version": "1.0"}
        }
    }
    
    req_bytes = json.dumps(init_req).encode('utf-8') + b"\n"
    
    try:
        process.stdin.write(req_bytes)
        process.stdin.flush()
        console.print("  → Initialize 요청 전송")
    except Exception as e:
        console.print(f"[red]✗ 전송 실패: {e}[/red]")
        process.kill()
        return
        
    # 응답 대기
    def read_stderr():
        while True:
            line = process.stderr.readline()
            if not line: break
            console.print(f"[dim]  [STDERR] {line.decode('utf-8', errors='replace').strip()}[/dim]")
            
    threading.Thread(target=read_stderr, daemon=True).start()
    
    try:
        # 3초 타임아웃
        start_time = time.time()
        while time.time() - start_time < 3:
            if process.poll() is not None:
                console.print(f"[red]✗ 프로세스가 조기 종료됨 (Exit Code: {process.returncode})[/red]")
                break
                
            line = process.stdout.readline()
            if line:
                try:
                    resp = json.loads(line.decode('utf-8'))
                    if "result" in resp:
                        console.print("[bold green]✅ 서버 초기화 응답 성공![/bold green]")
                        console.print(f"  Server: {resp['result'].get('serverInfo', {}).get('name')}")
                        console.print(f"  Version: {resp['result'].get('serverInfo', {}).get('version')}")
                    elif "error" in resp:
                        console.print(f"[red]✗ 서버 에러: {resp['error']}[/red]")
                    else:
                        console.print(f"[yellow]⚠ 알 수 없는 응답:[/yellow] {line}")
                    break
                except json.JSONDecodeError:
                    console.print(f"[red]✗ 잘못된 JSON 응답:[/red] {line}")
                    break
            time.sleep(0.1)
        else:
             console.print("[red]✗ 응답 시간 초과 (3초)[/red]")
             process.kill()
             
    except Exception as e:
         console.print(f"[red]✗ 응답 읽기 실패: {e}[/red]")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except:
                process.kill()


# === 헬퍼 함수 ===

def _ensure_directories():
    """필요한 디렉토리 생성"""
    DEFAULT_GEMINI_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_SISYPHUS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _create_full_backup(backup_id: Optional[str] = None) -> Optional[str]:
    """전체 설정 백업"""
    if backup_id is None:
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    backup_path = BACKUP_DIR / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    files_backed_up = []
    
    # GEMINI.md 백업
    if GEMINI_MD_PATH.exists():
        shutil.copy2(GEMINI_MD_PATH, backup_path / "GEMINI.md")
        files_backed_up.append("GEMINI.md")
    
    # MCP 설정 백업
    if MCP_CONFIG_PATH.exists():
        shutil.copy2(MCP_CONFIG_PATH, backup_path / "mcp_config.json")
        files_backed_up.append("mcp_config.json")
    
    # 상태 파일 백업
    if DEFAULT_SISYPHUS_DIR.exists():
        for json_file in DEFAULT_SISYPHUS_DIR.glob("*.json"):
            shutil.copy2(json_file, backup_path / json_file.name)
            files_backed_up.append(json_file.name)
    
    if not files_backed_up:
        # 백업할 파일 없음
        shutil.rmtree(backup_path)
        return None
    
    # 메타데이터 저장
    meta = {
        "backup_id": backup_id,
        "created_at": datetime.now().isoformat(),
        "files": files_backed_up,
        "type": "full"
    }
    with open(backup_path / "_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    return backup_id


def _install_gemini_md(force: bool) -> dict:
    """GEMINI.md 설치"""
    if GEMINI_MD_PATH.exists() and not force:
        # 이미 Sisyphus 설정이 있는지 확인
        with open(GEMINI_MD_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "Oh-My-Antigravity-Sisyphus" in content:
            return {"success": True, "message": "이미 설치됨"}
        else:
            return {"success": False, "message": "기존 GEMINI.md 존재 (--force로 덮어쓰기)"}
    
    # 템플릿 경로 찾기
    template_path = get_template_path()
    
    if template_path and template_path.exists():
        shutil.copy2(template_path, GEMINI_MD_PATH)
        return {"success": True, "message": "GEMINI.md 설치됨"}
    else:
        # 템플릿이 없으면 기본 내용 생성
        # (이미 사용자 환경에 GEMINI.md가 있으므로 이 경우는 드물음)
        return {"success": False, "message": "템플릿 파일을 찾을 수 없음"}


def _install_mcp_config(force: bool) -> dict:
    """MCP 설정 추가"""
    # Python 실행 경로 확인
    import sys
    python_path = sys.executable
    
    sisyphus_config = {
        "command": python_path,
        "args": [
            "-u",           # Unbuffered stdout/stderr
            "-W", "ignore", # RuntimeWarning 숨김
            "-m", "sisyphus_mcp.server"
        ],
        "env": {
            "SISYPHUS_STATE_DIR": str(DEFAULT_SISYPHUS_DIR),
            "PYTHONUTF8": "1",           # UTF-8 모드 강제
            "PYTHONIOENCODING": "utf-8"  # IO 인코딩 강제
        }
    }
    
    if MCP_CONFIG_PATH.exists():
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    config = json.loads(content)
                else:
                    config = {}
        except json.JSONDecodeError:
            config = {}
    else:
        config = {}
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    if "sisyphus-hooks" in config["mcpServers"] and not force:
        return {"success": True, "message": "이미 등록됨"}
    
    config["mcpServers"]["sisyphus-hooks"] = sisyphus_config
    
    with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return {"success": True, "message": "MCP 서버 등록됨"}


if __name__ == "__main__":
    cli()
