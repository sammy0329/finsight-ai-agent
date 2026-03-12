"""T-219, T-224, T-225: AgentExecutor 통합 테스트."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import MagicMock, patch

import pytest


class TestCreateAgentExecutor:
    """AgentExecutor 생성 테스트."""

    @patch("app.agent.executor.ChatOpenAI")
    @patch("app.agent.executor.create_openai_tools_agent")
    @patch("app.agent.executor.AgentExecutor")
    def test_creates_executor_for_segment_a(
        self, mock_agent_executor, mock_create_agent, mock_llm_cls
    ):
        """세그먼트 A에 대해 AgentExecutor를 생성한다."""
        from app.agent.executor import create_agent_executor

        mock_agent_executor.return_value = MagicMock()

        executor = create_agent_executor(
            segment="A",
            openai_api_key="test-key",
            chroma_host="localhost",
            chroma_port=8001,
        )

        assert executor is not None

    @patch("app.agent.executor.ChatOpenAI")
    @patch("app.agent.executor.create_openai_tools_agent")
    @patch("app.agent.executor.AgentExecutor")
    def test_creates_executor_for_segment_b(
        self, mock_agent_executor, mock_create_agent, mock_llm_cls
    ):
        """세그먼트 B에 대해 AgentExecutor를 생성한다."""
        from app.agent.executor import create_agent_executor

        mock_agent_executor.return_value = MagicMock()

        executor = create_agent_executor(
            segment="B",
            openai_api_key="test-key",
            chroma_host="localhost",
            chroma_port=8001,
        )

        assert executor is not None

    @patch("app.agent.executor.ChatOpenAI")
    @patch("app.agent.executor.create_openai_tools_agent")
    @patch("app.agent.executor.AgentExecutor")
    def test_creates_executor_for_segment_c(
        self, mock_agent_executor, mock_create_agent, mock_llm_cls
    ):
        """세그먼트 C에 대해 AgentExecutor를 생성한다."""
        from app.agent.executor import create_agent_executor

        mock_agent_executor.return_value = MagicMock()

        executor = create_agent_executor(
            segment="C",
            openai_api_key="test-key",
            chroma_host="localhost",
            chroma_port=8001,
        )

        assert executor is not None

    @patch("app.agent.executor.ChatOpenAI")
    @patch("app.agent.executor.create_openai_tools_agent")
    @patch("app.agent.executor.AgentExecutor")
    def test_uses_correct_prompt_for_segment(
        self, mock_agent_executor_cls, mock_create_agent, mock_llm_cls
    ):
        """세그먼트에 맞는 프롬프트를 사용한다."""
        from app.agent.executor import create_agent_executor

        mock_agent_executor_cls.return_value = MagicMock()

        create_agent_executor(
            segment="A",
            openai_api_key="test-key",
            chroma_host="localhost",
            chroma_port=8001,
        )

        # create_openai_tools_agent에 전달된 prompt 확인
        mock_create_agent.assert_called_once()
        call_kwargs = mock_create_agent.call_args
        prompt = call_kwargs[1].get("prompt") or call_kwargs[0][2]
        # prompt가 전달되었는지 확인
        assert prompt is not None

    @patch("app.agent.executor.ChatOpenAI")
    @patch("app.agent.executor.create_openai_tools_agent")
    @patch("app.agent.executor.AgentExecutor")
    def test_includes_four_tools(self, mock_agent_executor_cls, mock_create_agent, mock_llm_cls):
        """4개의 도구가 Agent에 등록된다."""
        from app.agent.executor import create_agent_executor

        mock_agent_executor_cls.return_value = MagicMock()

        create_agent_executor(
            segment="A",
            openai_api_key="test-key",
            chroma_host="localhost",
            chroma_port=8001,
        )

        call_kwargs = mock_create_agent.call_args
        tools = call_kwargs[1].get("tools") or call_kwargs[0][1]
        assert len(tools) == 4

    def test_raises_on_invalid_segment(self):
        """유효하지 않은 세그먼트에서 ValueError를 발생시킨다."""
        from app.agent.executor import create_agent_executor

        with pytest.raises(ValueError, match="Unknown segment"):
            create_agent_executor(
                segment="D",
                openai_api_key="test-key",
            )


class TestAgentPromptSegments:
    """T-224: 세그먼트별 Agent 프롬프트 테스트."""

    def test_agent_prompt_a_contains_tools_instruction(self):
        """A형 Agent 프롬프트에 도구 사용 지침이 포함된다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        prompt = get_agent_prompt_for_segment("A")
        # Agent 프롬프트는 도구 사용을 안내해야 한다
        prompt_text = str(prompt.messages[0].prompt.template)
        assert "도구" in prompt_text or "tool" in prompt_text.lower()

    def test_agent_prompt_b_contains_tools_instruction(self):
        """B형 Agent 프롬프트에 도구 사용 지침이 포함된다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        prompt = get_agent_prompt_for_segment("B")
        prompt_text = str(prompt.messages[0].prompt.template)
        assert "도구" in prompt_text or "tool" in prompt_text.lower()

    def test_agent_prompt_preserves_segment_personality(self):
        """Agent 프롬프트가 세그먼트별 성격을 유지한다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        prompt_a = get_agent_prompt_for_segment("A")
        prompt_b = get_agent_prompt_for_segment("B")

        text_a = str(prompt_a.messages[0].prompt.template)
        text_b = str(prompt_b.messages[0].prompt.template)

        # A형은 보수적 키워드, B형은 공격적 키워드
        assert any(kw in text_a for kw in ("보수", "안전", "리스크"))
        assert any(kw in text_b for kw in ("성장", "공격", "모멘텀"))

    def test_agent_prompt_has_agent_scratchpad(self):
        """Agent 프롬프트에 agent_scratchpad 변수가 포함된다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        prompt = get_agent_prompt_for_segment("A")
        input_vars = prompt.input_variables
        assert "agent_scratchpad" in input_vars

    def test_agent_prompt_has_input_variable(self):
        """Agent 프롬프트에 input 변수가 포함된다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        prompt = get_agent_prompt_for_segment("A")
        input_vars = prompt.input_variables
        assert "input" in input_vars

    def test_agent_prompt_raises_on_invalid_segment(self):
        """유효하지 않은 세그먼트에서 ValueError를 발생시킨다."""
        from app.agent.prompts import get_agent_prompt_for_segment

        with pytest.raises(ValueError, match="Unknown segment"):
            get_agent_prompt_for_segment("X")


class TestAstreamAgent:
    """astream_agent 스트리밍 테스트."""

    @pytest.mark.asyncio
    async def test_streams_tokens(self):
        """AgentExecutor 스트리밍이 토큰을 yield한다."""
        from app.agent.executor import astream_agent

        mock_executor = MagicMock()

        async def mock_astream_events(input_dict, version, **kwargs):
            events = [
                {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="안녕")}},
                {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="하세요")}},
            ]
            for e in events:
                yield e

        mock_executor.astream_events = mock_astream_events

        tokens = []
        async for token in astream_agent(mock_executor, "테스트 질문"):
            tokens.append(token)

        assert len(tokens) >= 2
        assert "안녕" in tokens
        assert "하세요" in tokens

    @pytest.mark.asyncio
    async def test_handles_empty_stream(self):
        """빈 스트림을 처리한다."""
        from app.agent.executor import astream_agent

        mock_executor = MagicMock()

        async def mock_astream_events(input_dict, version, **kwargs):
            return
            yield  # noqa: PT004

        mock_executor.astream_events = mock_astream_events

        tokens = []
        async for token in astream_agent(mock_executor, "테스트"):
            tokens.append(token)

        assert tokens == []
