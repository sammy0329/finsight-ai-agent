"""T-201, T-212, T-213, T-225: FastAPI 라우터 정의 및 RAG 체인/Agent 연결."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.agent.chain import build_rag_chain, invoke_with_fallback
from app.agent.executor import astream_agent, create_agent_executor
from app.agent.retriever import get_retriever
from app.agent.tools import detect_price_anomaly_json
from app.api.schemas import InsightRequest, InsightResponse
from app.core.config import settings
from app.core.middleware import verify_internal_key

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _market_for_segment(segment: str) -> str:
    """세그먼트에 따라 시장 코드를 반환한다."""
    return "KOR" if segment in ("A", "C") else "US"


@router.post("/insight", response_model=InsightResponse)
async def get_insight(
    req: InsightRequest,
    _: str = Depends(verify_internal_key),
) -> InsightResponse:
    """AI 인사이트를 생성한다.

    Args:
        req: 인사이트 요청 (user_segment, query).

    Returns:
        InsightResponse: RAG 체인 기반 인사이트 응답.
    """
    retriever = get_retriever(
        chroma_host=settings.chroma_host,
        chroma_port=settings.chroma_port,
        market=_market_for_segment(req.user_segment),
    )
    chain = build_rag_chain(req.user_segment, retriever, settings.openai_api_key)
    insight = invoke_with_fallback(chain, retriever, req.query)

    source_docs = retriever.invoke(req.query)
    sources = list(
        {doc.metadata.get("source", "") for doc in source_docs if doc.metadata.get("source")}
    )

    return InsightResponse(insight=insight, sources=sources)


@router.post("/insight/stream")
async def get_insight_stream(
    req: InsightRequest,
    _: str = Depends(verify_internal_key),
):
    """StreamingResponse로 AgentExecutor 응답을 스트리밍한다.

    Args:
        req: 인사이트 요청 (user_segment, query).

    Returns:
        StreamingResponse: text/event-stream 형식의 스트리밍 응답.
    """
    executor = create_agent_executor(
        segment=req.user_segment,
        openai_api_key=settings.openai_api_key,
        chroma_host=settings.chroma_host,
        chroma_port=settings.chroma_port,
    )

    async def generate():
        async for token in astream_agent(executor, req.query):
            # 개행 포함 토큰은 <br> 치환 후 SSE 포맷으로 전송
            safe = token.replace("\n", "<br>")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/anomaly/{ticker}")
async def get_price_anomaly(
    ticker: str,
    _: str = Depends(verify_internal_key),
) -> dict:
    """가격 이상 감지 결과를 구조화된 JSON으로 반환한다.

    Args:
        ticker: 종목 티커 (예: 005930, AAPL).

    Returns:
        is_anomaly, zscore, direction, latest_return_pct, message 포함 dict.
    """
    return detect_price_anomaly_json(ticker)
