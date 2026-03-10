"""T-211, T-214: RAG 체인 구성 및 폴백 처리.

세그먼트별 프롬프트와 retriever로 LCEL 방식의 RAG 체인을 구성한다.
"""

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.agent.prompts import get_prompt_for_segment

FALLBACK_MESSAGE = "현재 관련 금융 데이터가 없습니다. 잠시 후 다시 시도해주세요."


def format_docs(docs: list[Document]) -> str:
    """검색된 Document 리스트를 문자열로 포맷한다.

    Args:
        docs: LangChain Document 리스트.

    Returns:
        개행 두 줄로 연결된 문서 내용 문자열.
    """
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(segment: str, retriever, openai_api_key: str):
    """세그먼트에 맞는 프롬프트와 retriever로 RAG 체인을 구성한다.

    Args:
        segment: 투자 성향 세그먼트 코드 ("A", "B", "C").
        retriever: LangChain retriever 인스턴스.
        openai_api_key: OpenAI API 키.

    Returns:
        LCEL 방식으로 구성된 RAG 체인 (Runnable).
    """
    prompt = get_prompt_for_segment(segment)
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)

    chain = (
        {"context": retriever | format_docs, "query": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def invoke_with_fallback(chain, retriever, query: str) -> str:
    """retriever 검색 결과가 없으면 폴백 메시지를 반환한다.

    Args:
        chain: LCEL RAG 체인.
        retriever: LangChain retriever 인스턴스.
        query: 사용자 질의 문자열.

    Returns:
        체인 실행 결과 또는 폴백 메시지.
    """
    docs = retriever.invoke(query)
    if not docs:
        return FALLBACK_MESSAGE
    return chain.invoke(query)
