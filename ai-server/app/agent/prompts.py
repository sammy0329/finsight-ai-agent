"""Epic 2-2: 세그먼트별 프롬프트 설계 (T-205 ~ T-209).

투자 성향 세그먼트(A/B/C)에 따라 맞춤형 시스템 프롬프트를 제공한다.
- A형 (안전추구형): 보수적, 리스크 강조, 배당/국채/안전자산 중심
- B형 (위험감수형): 공격적, 기회 강조, 성장주/모멘텀/테마주 중심
- C형 (가치투자형): 분석적, 장기 관점, 펀더멘털/실적/밸류에이션 중심
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# T-206: 안전추구형 (A형) 시스템 프롬프트
_SEGMENT_A_PROMPT = (
    "당신은 보수적인 투자 성향을 가진 고객을 위한 금융 AI 어시스턴트입니다.\n"
    "리스크를 최소화하는 관점에서 분석하고, "
    "배당주·채권·안전자산을 중심으로 인사이트를 제공하세요.\n"
    "손실 가능성을 명확히 언급하고, 안정적인 수익을 추구하는 방향으로 조언하세요."
)

# T-207: 위험감수형 (B형) 시스템 프롬프트
_SEGMENT_B_PROMPT = (
    "당신은 공격적인 투자 성향을 가진 고객을 위한 금융 AI 어시스턴트입니다.\n"
    "시장의 성장 기회와 모멘텀을 강조하고, "
    "성장주·테마주·고수익 자산을 중심으로 인사이트를 제공하세요.\n"
    "단기 변동성보다 중장기 수익 잠재력에 초점을 맞추어 분석하세요."
)

# T-208: 가치투자형 (C형) 시스템 프롬프트
_SEGMENT_C_PROMPT = (
    "당신은 가치투자 성향을 가진 고객을 위한 금융 AI 어시스턴트입니다.\n"
    "기업의 펀더멘털과 내재가치를 분석하고, "
    "장기적 관점에서 저평가된 자산을 중심으로 인사이트를 제공하세요.\n"
    "실적, 재무제표, 밸류에이션 지표를 근거로 분석하세요."
)

# T-205: 세그먼트별 시스템 프롬프트 딕셔너리
SEGMENT_SYSTEM_PROMPTS: dict[str, str] = {
    "A": _SEGMENT_A_PROMPT,
    "B": _SEGMENT_B_PROMPT,
    "C": _SEGMENT_C_PROMPT,
}

# T-205: Human 메시지 템플릿 (모든 세그먼트 공용)
HUMAN_TEMPLATE = """다음 금융 뉴스 컨텍스트를 참고하여 질문에 답변해주세요.

컨텍스트:
{context}

질문: {query}

답변:"""


def get_prompt_for_segment(segment: str) -> ChatPromptTemplate:
    """세그먼트 코드(A/B/C)에 맞는 ChatPromptTemplate을 반환한다.

    Args:
        segment: 투자 성향 세그먼트 코드. "A"(안전추구형), "B"(위험감수형), "C"(가치투자형).

    Returns:
        system + human 메시지로 구성된 ChatPromptTemplate.

    Raises:
        ValueError: 알 수 없는 세그먼트 코드가 입력된 경우.
    """
    system_prompt = SEGMENT_SYSTEM_PROMPTS.get(segment)
    if not system_prompt:
        raise ValueError(f"Unknown segment: {segment!r}. Must be one of: A, B, C")
    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", HUMAN_TEMPLATE),
        ]
    )


# ── T-224: Agent 전용 세그먼트별 프롬프트 ────────────────────────────

_AGENT_TOOL_INSTRUCTION = (
    "\n\n당신은 다음 도구를 활용할 수 있습니다:\n"
    "1. search_news_tool: 관련 금융 뉴스 검색\n"
    "2. get_dart_tool: DART 공시 목록 조회\n"
    "3. get_price_tool: Yahoo Finance 실시간 가격 조회\n"
    "4. price_anomaly_tool: 가격 이상(Z-score) 감지\n\n"
    "질문에 답변하기 위해 필요한 도구를 적절히 선택하여 사용하세요.\n"
    "도구 결과를 종합하여 세그먼트에 맞는 투자 인사이트를 제공하세요."
)

AGENT_HUMAN_TEMPLATE = "{input}"


def get_agent_prompt_for_segment(segment: str) -> ChatPromptTemplate:
    """세그먼트 코드(A/B/C)에 맞는 Agent용 ChatPromptTemplate을 반환한다.

    기존 세그먼트 프롬프트에 도구 사용 지침을 추가하고,
    agent_scratchpad를 포함하는 Agent 전용 프롬프트를 생성한다.

    Args:
        segment: 투자 성향 세그먼트 코드. "A", "B", "C".

    Returns:
        Agent 실행에 필요한 ChatPromptTemplate (input, agent_scratchpad 포함).

    Raises:
        ValueError: 알 수 없는 세그먼트 코드가 입력된 경우.
    """
    system_prompt = SEGMENT_SYSTEM_PROMPTS.get(segment)
    if not system_prompt:
        raise ValueError(f"Unknown segment: {segment!r}. Must be one of: A, B, C")

    full_system = system_prompt + _AGENT_TOOL_INSTRUCTION

    return ChatPromptTemplate.from_messages(
        [
            ("system", full_system),
            ("human", AGENT_HUMAN_TEMPLATE),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
