"""
Keyword Detection for Sisyphus MCP.
Detects magic keywords in prompts to activate enhanced modes.
"""

import re
from typing import NamedTuple


class KeywordMatch(NamedTuple):
    """키워드 매치 결과"""
    keyword: str
    type: str
    position: int


# 매직 키워드 정의
KEYWORDS = {
    "ultrawork": {
        "triggers": ["ultrawork", "ulw", "uw", "울트라워크"],
        "type": "ultrawork",
        "priority": 1
    },
    "ultrathink": {
        "triggers": ["ultrathink", "think", "reason", "ponder", "생각", "추론"],
        "type": "ultrathink",
        "priority": 2
    },
    "search": {
        "triggers": [
            "search", "find", "locate", "lookup", "explore", "discover",
            "scan", "grep", "query", "browse", "detect", "trace", "seek",
            "track", "pinpoint", "hunt", "찾아", "검색"
        ],
        "type": "search",
        "priority": 3
    },
    "analyze": {
        "triggers": [
            "analyze", "analyse", "investigate", "examine", "research",
            "study", "deep-dive", "inspect", "audit", "evaluate", "assess",
            "review", "diagnose", "scrutinize", "dissect", "debug",
            "comprehend", "interpret", "breakdown", "understand",
            "분석", "조사"
        ],
        "type": "analyze",
        "priority": 4
    }
}

# 코드 블록 패턴 (키워드 감지에서 제외)
CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_PATTERN = re.compile(r"`[^`]+`")


def remove_code_blocks(text: str) -> str:
    """코드 블록 제거 (오탐 방지)"""
    text = CODE_BLOCK_PATTERN.sub("", text)
    text = INLINE_CODE_PATTERN.sub("", text)
    return text


def detect_keywords(text: str) -> list[KeywordMatch]:
    """
    텍스트에서 매직 키워드 감지
    
    Args:
        text: 검사할 텍스트
        
    Returns:
        감지된 키워드 목록 (우선순위 순)
    """
    # 코드 블록 제거
    cleaned_text = remove_code_blocks(text)
    lower_text = cleaned_text.lower()
    
    matches = []
    
    for keyword_name, keyword_def in KEYWORDS.items():
        for trigger in keyword_def["triggers"]:
            # 단어 경계 포함 검색 (일부 트리거만)
            # 한글은 단어 경계 검사 어려움
            pattern = rf"\b{re.escape(trigger)}\b" if trigger.isascii() else trigger
            
            for match in re.finditer(pattern, lower_text, re.IGNORECASE):
                matches.append(KeywordMatch(
                    keyword=trigger,
                    type=keyword_def["type"],
                    position=match.start()
                ))
    
    # 중복 타입 제거 (우선순위 순)
    seen_types = set()
    unique_matches = []
    
    # 우선순위 정렬
    priority_order = {"ultrawork": 1, "ultrathink": 2, "search": 3, "analyze": 4}
    matches.sort(key=lambda m: priority_order.get(m.type, 99))
    
    for match in matches:
        if match.type not in seen_types:
            seen_types.add(match.type)
            unique_matches.append(match)
    
    return unique_matches


def get_enhancement_message(keyword_type: str) -> str:
    """
    키워드 타입에 해당하는 개선 메시지 반환
    
    Args:
        keyword_type: 키워드 타입 (ultrawork, ultrathink, search, analyze)
        
    Returns:
        시스템 메시지
    """
    messages = {
        "ultrawork": """
🚀 **ULTRAWORK 모드 활성화**

## 행동 규칙
1. **병렬 작업 우선** - 독립적인 작업은 동시에 실행
2. **적극적 위임** - 복잡한 작업은 분해하여 진행
3. **중단 전 검증 필수**

## 체크리스트 (중단 전 확인)
- [ ] TODO LIST: 미완료 작업 제로
- [ ] FUNCTIONALITY: 모든 기능 동작
- [ ] TESTS: 테스트 통과
- [ ] ERRORS: 미해결 에러 제로

**하나라도 미완료면 계속 작업!**
""",
        "ultrathink": """
🧠 **ULTRATHINK 모드 활성화**

심층 분석 및 추론 모드입니다.
- 단계별 논리 전개
- 가정 명시
- 장단점 분석
- 대안 제시
""",
        "search": """
🔍 **심층 검색 모드 활성화**

철저한 검색을 수행합니다:
- 여러 검색 전략 병행
- 관련 파일 전체 탐색
- 의존성 추적
- 결과 교차 검증
""",
        "analyze": """
🔬 **심층 분석 모드 활성화**

깊이 있는 분석을 수행합니다:
- 근본 원인 파악
- 영향 범위 분석
- 해결 방안 제시
- 리스크 평가
"""
    }
    
    return messages.get(keyword_type, "")


def process_prompt(text: str) -> tuple[str, list[KeywordMatch]]:
    """
    프롬프트 처리 - 키워드 감지 및 메시지 생성
    
    Args:
        text: 원본 프롬프트
        
    Returns:
        (처리된 프롬프트, 감지된 키워드)
    """
    keywords = detect_keywords(text)
    
    if not keywords:
        return text, []
    
    # 최우선 키워드의 메시지 추가
    primary_keyword = keywords[0]
    enhancement = get_enhancement_message(primary_keyword.type)
    
    if enhancement:
        processed = f"{enhancement}\n\n---\n\n{text}"
        return processed, keywords
    
    return text, keywords
