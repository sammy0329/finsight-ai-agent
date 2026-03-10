"""T-202: 요청/응답 Pydantic 스키마 정의."""

from typing import Literal

from pydantic import BaseModel


class InsightRequest(BaseModel):
    """AI 인사이트 요청 스키마."""

    user_segment: Literal["A", "B", "C"]
    query: str


class InsightResponse(BaseModel):
    """AI 인사이트 응답 스키마."""

    insight: str
    sources: list[str]
