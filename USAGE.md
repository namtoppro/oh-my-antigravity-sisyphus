# 🪨 Oh-My-Antigravity-Sisyphus 사용 가이드

> Antigravity IDE를 위한 멀티 에이전트 오케스트레이션 시스템

---

## 📦 설치

### 요구 사항
- Python 3.10 이상
- Antigravity IDE

### 설치 방법

```bash
# 패키지 설치
pip install sisyphus-mcp

# Antigravity에 설정 적용 (기존 설정 자동 백업됨)
sisyphus-mcp install
```

> ⚠️ **자동 백업**: 설치 시 기존 `GEMINI.md`와 `mcp_config.json`이 자동으로 백업됩니다.

설치 후 **Antigravity IDE를 재시작**하세요.

---

## 🚀 빠른 시작

### 1. Ultrawork 모드 활성화

프롬프트에 `ultrawork` 키워드를 포함하면 최대 성능 모드가 활성화됩니다:

```
ultrawork: 프로젝트의 인증 모듈을 리팩토링해주세요
```

**지원 키워드:**
- `ultrawork`, `ulw`, `uw` (영문)
- `울트라워크` (한글)

### 2. 작업 완료 검증

작업 종료 전 반드시 완료 상태를 확인하세요:

```
sisyphus_verify_completion 도구를 호출해서 완료 상태를 확인해줘
```

---

## 🔧 CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `sisyphus-mcp install` | 설치 (자동 백업 포함) |
| `sisyphus-mcp uninstall` | 제거 |
| `sisyphus-mcp backup` | 현재 설정 백업 |
| `sisyphus-mcp restore [ID]` | 백업에서 복구 |
| `sisyphus-mcp list-backups` | 백업 목록 |
| `sisyphus-mcp status` | 설치 상태 확인 |
| `sisyphus-mcp doctor` | 연결 상태 진단 |

### 예시

```bash
# 설치 상태 확인
sisyphus-mcp status

# 백업 생성
sisyphus-mcp backup

# 백업 목록 확인
sisyphus-mcp list-backups

# 특정 백업으로 복구
sisyphus-mcp restore 20260116_153157
```

---

## 🎯 MCP 도구

Antigravity에서 사용 가능한 10개의 MCP 도구:

### 작업 관리

| 도구 | 설명 | 사용 시점 |
|------|------|----------|
| `sisyphus_start_task` | 새 작업 시작 | 복잡한 작업 시작 시 |
| `sisyphus_add_todo` | TODO 항목 추가 | 서브태스크 추가 |
| `sisyphus_check_todos` | TODO 목록 확인 | 진행 상황 확인 |
| `sisyphus_complete_todo` | TODO 완료 표시 | 서브태스크 완료 시 |
| `sisyphus_verify_completion` | **완료 검증** | **작업 종료 전 필수** |

### 모드 관리

| 도구 | 설명 |
|------|------|
| `sisyphus_activate_ultrawork` | Ultrawork 모드 활성화 |
| `sisyphus_deactivate_ultrawork` | Ultrawork 모드 비활성화 |
| `sisyphus_get_context` | 세션 컨텍스트 로드 |
| `sisyphus_start_ralph_loop` | Ralph Loop 시작 |
| `sisyphus_end_ralph_loop` | Ralph Loop 종료 |

---

## 📊 매직 키워드

프롬프트에 다음 키워드를 포함하면 해당 모드가 활성화됩니다:

| 키워드 | 효과 |
|--------|------|
| `ultrawork`, `ulw`, `uw`, `울트라워크` | 최대 성능 모드 |
| `search`, `find`, `찾아`, `검색` | 심층 검색 모드 |
| `analyze`, `investigate`, `분석`, `조사` | 심층 분석 모드 |
| `ultrathink`, `think`, `생각`, `추론` | 확장 사고 모드 |

---

## 🔀 Git Master 규칙

Sisyphus는 Git 커밋 분리를 강제합니다:

| 변경 파일 수 | 최소 커밋 수 |
|-------------|-------------|
| 3+ 파일 | 2+ 커밋 |
| 5+ 파일 | 3+ 커밋 |
| 10+ 파일 | 5+ 커밋 |

### 커밋 분리 기준
- 다른 디렉토리/모듈 → **분리**
- 다른 컴포넌트 타입 → **분리**
- 독립적 롤백 가능 → **분리**

---

## ⚠️ 중단 전 체크리스트

작업을 완료하기 전 반드시 확인하세요:

```
- [ ] TODO LIST: 미완료 작업 제로
- [ ] FUNCTIONALITY: 모든 요청 기능 동작
- [ ] TESTS: 해당 시 테스트 통과
- [ ] ERRORS: 미해결 에러 제로
```

**하나라도 미완료면 작업을 계속해야 합니다!**

---

## 🔄 백업 및 복구

### 자동 백업
`sisyphus-mcp install` 실행 시 기존 설정이 자동으로 백업됩니다.

### 수동 백업
```bash
sisyphus-mcp backup
```

### 복구
```bash
# 백업 목록 확인
sisyphus-mcp list-backups

# 복구
sisyphus-mcp restore 20260116_153157
```

### 백업 위치
- 전체 백업: `~/.gemini/.sisyphus/backups/`
- GEMINI.md 백업: `~/.gemini/GEMINI.md.backup.*`

---

## 📁 설정 파일 위치

| 파일 | 경로 |
|------|------|
| 시스템 프롬프트 | `~/.gemini/GEMINI.md` |
| MCP 설정 | `~/.gemini/antigravity/mcp_config.json` |
| 상태 저장소 | `~/.gemini/.sisyphus/` |

---

## ❓ 문제 해결

### MCP 도구가 보이지 않아요
1. `sisyphus-mcp doctor` 명령어로 진단을 수행하세요.
2. `sisyphus-mcp install --force`로 설정을 강제 갱신하세요. (최신 안정성 옵션 적용)
3. Antigravity IDE를 완전히 종료 후 재시작하세요.

### 백업에서 복구하고 싶어요
```bash
sisyphus-mcp list-backups
sisyphus-mcp restore [백업ID]
```

### 완전히 제거하고 싶어요
```bash
sisyphus-mcp uninstall
```

---

## 📄 라이선스

MIT License
