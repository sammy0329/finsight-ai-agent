"""T-219: LangChain AgentExecutor 기반 구조.

세그먼트별 프롬프트와 도구를 사용하는 AgentExecutor를 초기화한다.
"""

from __future__ import annotations

from typing import AsyncIterator

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

from app.agent.prompts import get_agent_prompt_for_segment
from app.agent.tools import (
    get_dart_tool,
    get_price_tool,
    price_anomaly_tool,
    search_news_tool,
)


def create_agent_executor(segment: str, openai_api_key: str, **kwargs) -> AgentExecutor:
    """세그먼트에 맞는 AgentExecutor를 생성한다.

    Args:
        segment: 투자 성향 세그먼트 코드 ("A", "B", "C").
        openai_api_key: OpenAI API 키.
        **kwargs: 추가 설정 (chroma_host, chroma_port, dart_api_key 등).

    Returns:
        LangChain AgentExecutor 인스턴스.

    Raises:
        ValueError: 유효하지 않은 세그먼트 코드.
    """
    prompt = get_agent_prompt_for_segment(segment)
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)

    tools = [search_news_tool, get_dart_tool, get_price_tool, price_anomaly_tool]

    agent = create_openai_tools_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
    )


async def astream_agent(executor: AgentExecutor, query: str) -> AsyncIterator[str]:
    """AgentExecutor를 스트리밍 모드로 실행한다.

    Args:
        executor: AgentExecutor 인스턴스.
        query: 사용자 질의.

    Yields:
        응답 토큰 문자열.
    """
    async for event in executor.astream_events(
        {"input": query},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            content = chunk.content
            if content:
                yield content
