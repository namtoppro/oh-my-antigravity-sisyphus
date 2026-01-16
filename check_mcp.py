import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 색상 코드
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CYAN = "\033[96m"

def print_step(msg):
    print(f"\n{CYAN}=== {msg} ==={RESET}")

def print_ok(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_warn(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def check_mcp():
    print_step("환경 정보")
    user_home = Path.home()
    print(f"User Home: {user_home}")
    
    # 1. 설정 파일 확인
    print_step("설정 파일 확인")
    config_path = user_home / ".gemini" / "antigravity" / "mcp_config.json"
    print(f"Config Path: {config_path}")
    
    if not config_path.exists():
        print_error("설정 파일이 없습니다!")
        return
    
    print_ok("설정 파일 존재함")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print_ok("JSON 파싱 성공")
        print(json.dumps(config, indent=2))
    except Exception as e:
        print_error(f"설정 파일 읽기 실패: {e}")
        return

    # 2. Sisyphus 설정 확인
    print_step("Sisyphus 설정 확인")
    sisyphus_conf = config.get("mcpServers", {}).get("sisyphus-hooks")
    
    if not sisyphus_conf:
        print_error("sisyphus-hooks 설정이 없습니다!")
        return
    
    print_ok("sisyphus-hooks 설정 발견")
    
    cmd = sisyphus_conf.get("command")
    args = sisyphus_conf.get("args", [])
    env_vars = sisyphus_conf.get("env", {})
    
    print(f"Command: {cmd}")
    print(f"Args: {args}")
    print(f"Env: {env_vars}")
    
    # Python 경로 확인
    if not Path(cmd).exists():
        print_error(f"Python 실행 파일을 찾을 수 없음: {cmd}")
    else:
        print_ok(f"Python 실행 파일 확인됨: {cmd}")

    # 3. 서버 실행 테스트
    print_step("서버 프로세스 실행 테스트")
    
    # 환경 변수 병합
    proc_env = os.environ.copy()
    proc_env.update(env_vars)
    
    full_cmd = [cmd] + args
    print(f"Executing: {' '.join(full_cmd)}")
    
    try:
        process = subprocess.Popen(
            full_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=proc_env,
            text=False  # 바이너리 모드
        )
        print_ok("프로세스 시작됨")
    except Exception as e:
        print_error(f"프로세스 실행 실패: {e}")
        return

    # 4. Initialize 요청 전송
    print_step("JSON-RPC Initialize 요청")
    
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-script", "version": "1.0"}
        }
    }
    
    req_json = json.dumps(init_request).encode('utf-8') + b"\n"
    
    try:
        print(f"Sending: {req_json}")
        process.stdin.write(req_json)
        process.stdin.flush()
        print_ok("요청 전송 완료")
    except Exception as e:
        print_error(f"요청 전송 실패: {e}")
        process.kill()
        return

    # 5. 응답 대기
    print_step("응답 대기 (3초)")
    
    import threading
    
    def read_stderr():
        while True:
            line = process.stderr.readline()
            if not line: break
            print(f"{YELLOW}[STDERR] {line.decode('utf-8', errors='replace').strip()}{RESET}")
            
    threading.Thread(target=read_stderr, daemon=True).start()
    
    try:
        # stdout 읽기 시도
        # 한 줄 읽기
        line = process.stdout.readline()
        if line:
            print(f"Received raw: {line}")
            try:
                resp = json.loads(line.decode('utf-8'))
                print_ok("JSON 응답 수신 성공")
                print(json.dumps(resp, indent=2, ensure_ascii=False))
                
                if "result" in resp:
                    print_ok("✅ 초기화 성공! 서버가 정상 작동합니다.")
                elif "error" in resp:
                    print_error(f"서버 에러 응답: {resp['error']}")
                
            except json.JSONDecodeError:
                print_error(f"잘못된 JSON 응답: {line}")
        else:
            print_error("응답 없음 (EOF)")
            
    except Exception as e:
        print_error(f"응답 읽기 중 에러: {e}")
    finally:
        print_step("테스트 종료")
        process.terminate()
        try:
            process.wait(timeout=1)
        except:
            process.kill()
        print("프로세스 종료됨")

if __name__ == "__main__":
    check_mcp()
