"""T-201: FastAPI 라우터 정의 및 엔드포인트 등록."""

from fastapi import APIRouter, Depends

from app.api.schemas import InsightRequest, InsightResponse
from app.core.middleware import verify_internal_key

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/insight", response_model=InsightResponse)
async def get_insight(
    req: InsightRequest,
    _: str = Depends(verify_internal_key),
) -> InsightResponse:
    """AI 인사이트를 생성한다 (placeholder).

    Args:
        req: 인사이트 요청 (user_segment, query).

    Returns:
        InsightResponse: placeholder 인사이트 응답.
    """
    return InsightResponse(
        insight=f"[{req.user_segment}] {req.query} 에 대한 인사이트 (구현 예정)",
        sources=[],
    )
