"""T-110: Pydantic 스키마 검증 모듈.

RAG 파이프라인에서 사용하는 데이터 모델을 정의하고 검증한다.
"""

import re

from pydantic import BaseModel, field_validator, model_validator

_METADATA_REQUIRED_FIELDS = [
    "source",
    "published_at",
    "collected_at",
    "market",
    "related_tickers",
    "category",
    "sentiment",
]


class NewsChunk(BaseModel):
    """뉴스 문서 청크 스키마.

    document는 비어있으면 안 되며, metadata에는 필수 필드가 모두 포함되어야 한다.
    """

    document: str
    metadata: dict

    @field_validator("document")
    @classmethod
    def document_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            msg = "document must not be empty or whitespace-only"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def metadata_must_have_required_fields(self) -> "NewsChunk":
        missing = [f for f in _METADATA_REQUIRED_FIELDS if f not in self.metadata]
        if missing:
            msg = f"metadata is missing required fields: {missing}"
            raise ValueError(msg)
        return self


class StockData(BaseModel):
    """주식 시세 데이터 스키마.

    ticker는 비어있으면 안 되며, date는 YYYY-MM-DD 형식이어야 한다.
    """

    ticker: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    @field_validator("ticker")
    @classmethod
    def ticker_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            msg = "ticker must not be empty"
            raise ValueError(msg)
        return v

    @field_validator("date")
    @classmethod
    def date_must_be_valid_yyyy_mm_dd(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            msg = "date must be in YYYY-MM-DD format"
            raise ValueError(msg)
        # 실제 유효한 날짜인지 검증
        _year, month, day = int(v[:4]), int(v[5:7]), int(v[8:10])
        if not (1 <= month <= 12):
            msg = f"invalid month: {month}"
            raise ValueError(msg)
        if not (1 <= day <= 31):
            msg = f"invalid day: {day}"
            raise ValueError(msg)
        # 월별 최대 일수 간단 검증
        days_in_month = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if day > days_in_month[month]:
            msg = f"invalid day {day} for month {month}"
            raise ValueError(msg)
        return v


class DartDisclosure(BaseModel):
    """DART 공시 데이터 스키마.

    모든 필드가 필수이며 빈 문자열을 허용하지 않는다.
    """

    title: str
    corp_name: str
    rcept_dt: str
    report_nm: str

    @field_validator("title", "corp_name")
    @classmethod
    def string_fields_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            msg = "field must not be empty"
            raise ValueError(msg)
        return v
