"""Epic 2-2: 세그먼트별 프롬프트 설계 테스트 (T-205 ~ T-209)."""

import pytest
from langchain_core.prompts import ChatPromptTemplate


class TestGetPromptForSegment:
    """T-209: 세그먼트 -> 프롬프트 팩토리 함수 테스트."""

    def test_returns_chat_prompt_template_for_segment_a(self):
        """A형(안전추구형) 세그먼트에 대해 ChatPromptTemplate을 반환한다."""
        from app.agent.prompts import get_prompt_for_segment

        result = get_prompt_for_segment("A")
        assert isinstance(result, ChatPromptTemplate)

    def test_returns_chat_prompt_template_for_segment_b(self):
        """B형(위험감수형) 세그먼트에 대해 ChatPromptTemplate을 반환한다."""
        from app.agent.prompts import get_prompt_for_segment

        result = get_prompt_for_segment("B")
        assert isinstance(result, ChatPromptTemplate)

    def test_returns_chat_prompt_template_for_segment_c(self):
        """C형(가치투자형) 세그먼트에 대해 ChatPromptTemplate을 반환한다."""
        from app.agent.prompts import get_prompt_for_segment

        result = get_prompt_for_segment("C")
        assert isinstance(result, ChatPromptTemplate)

    def test_raises_value_error_for_unknown_segment(self):
        """알 수 없는 세그먼트("D") 입력 시 ValueError가 발생한다."""
        from app.agent.prompts import get_prompt_for_segment

        with pytest.raises(ValueError, match="Unknown segment"):
            get_prompt_for_segment("D")

    def test_raises_value_error_for_empty_string(self):
        """빈 문자열 입력 시 ValueError가 발생한다."""
        from app.agent.prompts import get_prompt_for_segment

        with pytest.raises(ValueError, match="Unknown segment"):
            get_prompt_for_segment("")

    def test_raises_value_error_for_lowercase_segment(self):
        """소문자 세그먼트 입력 시 ValueError가 발생한다 (대문자만 허용)."""
        from app.agent.prompts import get_prompt_for_segment

        with pytest.raises(ValueError, match="Unknown segment"):
            get_prompt_for_segment("a")


class TestPromptTemplateStructure:
    """T-205: 프롬프트 템플릿 기반 구조 테스트."""

    def test_template_contains_context_variable(self):
        """반환된 템플릿에 context 변수가 포함되어 있다."""
        from app.agent.prompts import get_prompt_for_segment

        template = get_prompt_for_segment("A")
        input_vars = template.input_variables
        assert "context" in input_vars

    def test_template_contains_query_variable(self):
        """반환된 템플릿에 query 변수가 포함되어 있다."""
        from app.agent.prompts import get_prompt_for_segment

        template = get_prompt_for_segment("A")
        input_vars = template.input_variables
        assert "query" in input_vars

    def test_template_has_system_and_human_messages(self):
        """템플릿이 system + human 메시지 구조를 가진다."""
        from app.agent.prompts import get_prompt_for_segment

        template = get_prompt_for_segment("A")
        messages = template.messages
        assert len(messages) == 2
        # 첫 번째: system, 두 번째: human
        assert messages[0].prompt.template is not None
        assert messages[1].prompt.template is not None

    def test_format_messages_produces_valid_output(self):
        """format_messages로 실제 메시지를 생성할 수 있다."""
        from app.agent.prompts import get_prompt_for_segment

        template = get_prompt_for_segment("A")
        messages = template.format_messages(
            context="삼성전자 실적 발표: 매출 70조원 달성",
            query="삼성전자 투자 전망은?",
        )
        assert len(messages) == 2
        assert "삼성전자 실적 발표" in messages[1].content
        assert "삼성전자 투자 전망은?" in messages[1].content


class TestSegmentPromptsDiffer:
    """각 세그먼트 프롬프트가 서로 다른 내용인지 확인."""

    def test_all_segments_have_different_system_prompts(self):
        """A/B/C 세그먼트의 시스템 프롬프트가 모두 서로 다르다."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompts = list(SEGMENT_SYSTEM_PROMPTS.values())
        assert len(prompts) == 3
        assert prompts[0] != prompts[1]
        assert prompts[1] != prompts[2]
        assert prompts[0] != prompts[2]

    def test_all_segments_share_same_human_template(self):
        """모든 세그먼트가 동일한 human 템플릿을 공유한다."""
        from app.agent.prompts import get_prompt_for_segment

        templates = [get_prompt_for_segment(s) for s in ("A", "B", "C")]
        human_templates = [t.messages[1].prompt.template for t in templates]
        assert human_templates[0] == human_templates[1] == human_templates[2]


class TestSegmentAKeywords:
    """T-206: 안전추구형(A형) 시스템 프롬프트 키워드 테스트."""

    def test_contains_conservative_keywords(self):
        """A형 프롬프트에 '보수' 또는 '안전' 또는 '배당' 중 하나 이상 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["A"]
        assert any(kw in prompt for kw in ("보수", "안전", "배당")), (
            f"A형 프롬프트에 보수/안전/배당 키워드가 없습니다: {prompt}"
        )

    def test_contains_risk_awareness(self):
        """A형 프롬프트에 리스크/손실 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["A"]
        assert any(kw in prompt for kw in ("리스크", "손실", "위험")), (
            f"A형 프롬프트에 리스크 관련 키워드가 없습니다: {prompt}"
        )

    def test_contains_safe_asset_keywords(self):
        """A형 프롬프트에 채권/국채/안전자산 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["A"]
        assert any(kw in prompt for kw in ("채권", "국채", "안전자산")), (
            f"A형 프롬프트에 안전자산 관련 키워드가 없습니다: {prompt}"
        )


class TestSegmentBKeywords:
    """T-207: 위험감수형(B형) 시스템 프롬프트 키워드 테스트."""

    def test_contains_aggressive_keywords(self):
        """B형 프롬프트에 '성장' 또는 '모멘텀' 또는 '공격' 중 하나 이상 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["B"]
        assert any(kw in prompt for kw in ("성장", "모멘텀", "공격")), (
            f"B형 프롬프트에 성장/모멘텀/공격 키워드가 없습니다: {prompt}"
        )

    def test_contains_opportunity_keywords(self):
        """B형 프롬프트에 기회/수익 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["B"]
        assert any(kw in prompt for kw in ("기회", "수익", "잠재력")), (
            f"B형 프롬프트에 기회/수익 관련 키워드가 없습니다: {prompt}"
        )

    def test_contains_growth_asset_keywords(self):
        """B형 프롬프트에 성장주/테마주/고수익 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["B"]
        assert any(kw in prompt for kw in ("성장주", "테마주", "고수익")), (
            f"B형 프롬프트에 성장주/테마주 관련 키워드가 없습니다: {prompt}"
        )


class TestSegmentCKeywords:
    """T-208: 가치투자형(C형) 시스템 프롬프트 키워드 테스트."""

    def test_contains_value_keywords(self):
        """C형 프롬프트에 '펀더멘털' 또는 '가치' 또는 '실적' 중 하나 이상 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["C"]
        assert any(kw in prompt for kw in ("펀더멘털", "가치", "실적")), (
            f"C형 프롬프트에 펀더멘털/가치/실적 키워드가 없습니다: {prompt}"
        )

    def test_contains_analysis_keywords(self):
        """C형 프롬프트에 분석/재무 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["C"]
        assert any(kw in prompt for kw in ("분석", "재무", "밸류에이션")), (
            f"C형 프롬프트에 분석/재무 관련 키워드가 없습니다: {prompt}"
        )

    def test_contains_long_term_perspective(self):
        """C형 프롬프트에 장기/내재가치 관련 키워드 포함."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        prompt = SEGMENT_SYSTEM_PROMPTS["C"]
        assert any(kw in prompt for kw in ("장기", "내재가치", "저평가")), (
            f"C형 프롬프트에 장기적 관점 키워드가 없습니다: {prompt}"
        )


class TestHumanTemplate:
    """HUMAN_TEMPLATE 구조 테스트."""

    def test_human_template_contains_context_placeholder(self):
        """HUMAN_TEMPLATE에 {context} 플레이스홀더가 포함되어 있다."""
        from app.agent.prompts import HUMAN_TEMPLATE

        assert "{context}" in HUMAN_TEMPLATE

    def test_human_template_contains_query_placeholder(self):
        """HUMAN_TEMPLATE에 {query} 플레이스홀더가 포함되어 있다."""
        from app.agent.prompts import HUMAN_TEMPLATE

        assert "{query}" in HUMAN_TEMPLATE


class TestSegmentSystemPrompts:
    """SEGMENT_SYSTEM_PROMPTS 딕셔너리 구조 테스트."""

    def test_has_exactly_three_segments(self):
        """정확히 A, B, C 세 개의 세그먼트만 존재한다."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        assert set(SEGMENT_SYSTEM_PROMPTS.keys()) == {"A", "B", "C"}

    def test_all_prompts_are_non_empty_strings(self):
        """모든 프롬프트가 비어있지 않은 문자열이다."""
        from app.agent.prompts import SEGMENT_SYSTEM_PROMPTS

        for segment, prompt in SEGMENT_SYSTEM_PROMPTS.items():
            assert isinstance(prompt, str), f"Segment {segment} prompt is not a string"
            assert len(prompt.strip()) > 0, f"Segment {segment} prompt is empty"
