"""T-110: Pydantic 스키마 검증 모듈 테스트."""

import pytest
from pydantic import ValidationError

from app.pipeline.schemas import DartDisclosure, NewsChunk, StockData


# ================================================================== #
# NewsChunk
# ================================================================== #
class TestNewsChunk:
    """NewsChunk 스키마 검증 테스트."""

    def test_valid_news_chunk(self):
        """유효한 데이터로 생성할 수 있다."""
        chunk = NewsChunk(
            document="삼성전자 실적 발표",
            metadata={
                "source": "naver_news",
                "published_at": "2025-03-10T09:00:00",
                "collected_at": "2025-03-10T16:35:00",
                "market": "KOR",
                "related_tickers": ["005930"],
                "category": "general",
                "sentiment": "positive",
            },
        )
        assert chunk.document == "삼성전자 실적 발표"
        assert chunk.metadata["source"] == "naver_news"

    def test_empty_document_rejected(self):
        """document가 빈 문자열이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            NewsChunk(
                document="",
                metadata={
                    "source": "test",
                    "published_at": "2025-03-10T09:00:00",
                    "collected_at": "2025-03-10T16:35:00",
                    "market": "KOR",
                    "related_tickers": [],
                    "category": "general",
                    "sentiment": "neutral",
                },
            )

    def test_missing_metadata_required_fields(self):
        """metadata에 필수 필드가 빠지면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            NewsChunk(
                document="텍스트",
                metadata={"source": "test"},  # 나머지 필수 필드 누락
            )

    def test_whitespace_only_document_rejected(self):
        """공백만 있는 document도 빈 문자열로 취급하여 거부한다."""
        with pytest.raises(ValidationError):
            NewsChunk(
                document="   ",
                metadata={
                    "source": "test",
                    "published_at": "2025-03-10T09:00:00",
                    "collected_at": "2025-03-10T16:35:00",
                    "market": "KOR",
                    "related_tickers": [],
                    "category": "general",
                    "sentiment": "neutral",
                },
            )

    def test_metadata_must_be_dict(self):
        """metadata가 dict가 아니면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            NewsChunk(document="텍스트", metadata="not a dict")


# ================================================================== #
# StockData
# ================================================================== #
class TestStockData:
    """StockData 스키마 검증 테스트."""

    def test_valid_stock_data(self):
        """유효한 데이터로 생성할 수 있다."""
        stock = StockData(
            ticker="005930",
            date="2025-03-10",
            open=71000.0,
            high=72000.0,
            low=70500.0,
            close=71500.0,
            volume=15000000,
        )
        assert stock.ticker == "005930"
        assert stock.close == 71500.0

    def test_empty_ticker_rejected(self):
        """ticker가 빈 문자열이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            StockData(
                ticker="",
                date="2025-03-10",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000,
            )

    def test_invalid_date_format(self):
        """date가 YYYY-MM-DD 형식이 아니면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            StockData(
                ticker="005930",
                date="20250310",  # 잘못된 형식
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000,
            )

    def test_valid_date_formats(self):
        """올바른 YYYY-MM-DD 형식은 통과한다."""
        stock = StockData(
            ticker="AAPL",
            date="2025-01-01",
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1000,
        )
        assert stock.date == "2025-01-01"

    def test_negative_volume_accepted(self):
        """volume은 int이면 된다 (음수도 스키마 단계에서 허용)."""
        stock = StockData(
            ticker="AAPL",
            date="2025-03-10",
            open=100.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=-1,
        )
        assert stock.volume == -1

    def test_missing_required_field(self):
        """필수 필드가 없으면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            StockData(
                ticker="005930",
                date="2025-03-10",
                open=100.0,
                # high, low, close, volume 누락
            )

    def test_date_with_invalid_month(self):
        """유효하지 않은 월(13월 등)이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            StockData(
                ticker="AAPL",
                date="2025-13-10",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000,
            )

    def test_date_with_invalid_day(self):
        """유효하지 않은 일(32일 등)이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            StockData(
                ticker="AAPL",
                date="2025-03-32",
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000,
            )


# ================================================================== #
# DartDisclosure
# ================================================================== #
class TestDartDisclosure:
    """DartDisclosure 스키마 검증 테스트."""

    def test_valid_dart_disclosure(self):
        """유효한 데이터로 생성할 수 있다."""
        disc = DartDisclosure(
            title="사업보고서 (2024.12)",
            corp_name="삼성전자",
            rcept_dt="20250310",
            report_nm="사업보고서",
        )
        assert disc.title == "사업보고서 (2024.12)"
        assert disc.corp_name == "삼성전자"

    def test_empty_title_rejected(self):
        """title이 빈 문자열이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            DartDisclosure(
                title="",
                corp_name="삼성전자",
                rcept_dt="20250310",
                report_nm="사업보고서",
            )

    def test_empty_corp_name_rejected(self):
        """corp_name이 빈 문자열이면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            DartDisclosure(
                title="사업보고서",
                corp_name="",
                rcept_dt="20250310",
                report_nm="사업보고서",
            )

    def test_missing_required_field(self):
        """필수 필드가 누락되면 ValidationError가 발생한다."""
        with pytest.raises(ValidationError):
            DartDisclosure(
                title="사업보고서",
                # corp_name 누락
                rcept_dt="20250310",
                report_nm="사업보고서",
            )

    def test_all_fields_populated(self):
        """모든 필드가 올바르게 채워진다."""
        disc = DartDisclosure(
            title="분기보고서",
            corp_name="SK하이닉스",
            rcept_dt="20250315",
            report_nm="분기보고서",
        )
        assert disc.rcept_dt == "20250315"
        assert disc.report_nm == "분기보고서"
