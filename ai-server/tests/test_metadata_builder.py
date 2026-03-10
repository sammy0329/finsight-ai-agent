"""T-109: 메타데이터 부착 모듈 테스트."""

from unittest.mock import patch

from app.pipeline.metadata_builder import (
    build_news_metadata,
    detect_sentiment,
    extract_tickers,
)


# ================================================================== #
# detect_sentiment
# ================================================================== #
class TestDetectSentiment:
    """키워드 기반 감성 분류 테스트."""

    def test_positive_korean(self):
        """한국어 긍정 키워드를 감지한다."""
        assert detect_sentiment("삼성전자 실적 급등 소식") == "positive"

    def test_negative_korean(self):
        """한국어 부정 키워드를 감지한다."""
        assert detect_sentiment("반도체 업종 급락 위기") == "negative"

    def test_neutral_when_no_keywords(self):
        """감성 키워드가 없으면 neutral을 반환한다."""
        assert detect_sentiment("삼성전자 주주총회 안건 공개") == "neutral"

    def test_positive_english(self):
        """영어 긍정 키워드를 감지한다."""
        assert detect_sentiment("Stock market surge today") == "positive"

    def test_negative_english(self):
        """영어 부정 키워드를 감지한다."""
        assert detect_sentiment("Market bearish on tech loss") == "negative"

    def test_empty_string(self):
        """빈 문자열이면 neutral을 반환한다."""
        assert detect_sentiment("") == "neutral"

    def test_mixed_sentiment_positive_wins(self):
        """긍정/부정 키워드가 모두 있을 때 더 많은 쪽이 이긴다."""
        # 긍정 2개(상승, 성장) vs 부정 1개(하락)
        text = "상승 성장 하락"
        assert detect_sentiment(text) == "positive"

    def test_mixed_sentiment_tie_is_neutral(self):
        """긍정/부정 키워드 수가 같으면 neutral을 반환한다."""
        text = "상승 하락"
        assert detect_sentiment(text) == "neutral"


# ================================================================== #
# extract_tickers
# ================================================================== #
class TestExtractTickers:
    """종목 코드 추출 테스트."""

    def test_korean_6digit_ticker(self):
        """한국 시장 6자리 숫자 종목 코드를 추출한다."""
        text = "삼성전자(005930)가 상승했다."
        result = extract_tickers(text, "KOR")
        assert "005930" in result

    def test_korean_multiple_tickers(self):
        """한국 시장에서 여러 종목 코드를 추출한다."""
        text = "005930, 000660 종목이 급등"
        result = extract_tickers(text, "KOR")
        assert "005930" in result
        assert "000660" in result

    def test_us_ticker(self):
        """미국 시장 대문자 알파벳 2~5자 종목 코드를 추출한다."""
        text = "AAPL and MSFT are leading the market"
        result = extract_tickers(text, "US")
        assert "AAPL" in result
        assert "MSFT" in result

    def test_us_filters_common_words(self):
        """미국 시장에서 일반 영단어(THE, AND 등)는 제외한다."""
        text = "THE AAPL stock IS good FOR investors"
        result = extract_tickers(text, "US")
        assert "AAPL" in result
        assert "THE" not in result
        assert "FOR" not in result

    def test_korean_ignores_non_6digit_numbers(self):
        """한국 시장에서 6자리가 아닌 숫자는 무시한다."""
        text = "12345 종목과 1234567 종목"
        result = extract_tickers(text, "KOR")
        assert result == []

    def test_empty_string(self):
        """빈 문자열이면 빈 리스트를 반환한다."""
        assert extract_tickers("", "KOR") == []
        assert extract_tickers("", "US") == []

    def test_no_tickers_found(self):
        """종목 코드가 없으면 빈 리스트를 반환한다."""
        assert extract_tickers("아무 종목코드도 없는 텍스트", "KOR") == []

    def test_deduplicates_tickers(self):
        """같은 종목 코드가 여러 번 나오면 중복을 제거한다."""
        text = "005930 상승 005930 하락"
        result = extract_tickers(text, "KOR")
        assert result.count("005930") == 1


# ================================================================== #
# build_news_metadata
# ================================================================== #
class TestBuildNewsMetadata:
    """뉴스 메타데이터 생성 테스트."""

    SAMPLE_ITEM = {
        "title": "삼성전자(005930) 실적 급등 발표",
        "description": "삼성전자가 2025년 1분기 호실적을 발표했다.",
        "pubDate": "Mon, 10 Mar 2025 09:00:00 +0900",
        "link": "http://example.com/news/1",
    }

    def test_returns_required_keys(self):
        """반환 dict에 필수 키가 모두 포함된다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        required_keys = [
            "source",
            "published_at",
            "collected_at",
            "market",
            "related_tickers",
            "category",
            "sentiment",
        ]
        for key in required_keys:
            assert key in meta, f"Missing key: {key}"

    def test_source_field(self):
        """source 필드가 전달된 값과 일치한다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        assert meta["source"] == "naver_news"

    def test_market_field(self):
        """market 필드가 전달된 값과 일치한다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        assert meta["market"] == "KOR"

    def test_sentiment_detected(self):
        """sentiment가 올바르게 감지된다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        # "급등" + "호실적" -> positive
        assert meta["sentiment"] == "positive"

    def test_tickers_extracted(self):
        """related_tickers에 종목 코드가 추출된다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        assert "005930" in meta["related_tickers"]

    def test_collected_at_is_iso_format(self):
        """collected_at이 ISO 형식 문자열이다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        # ISO format: YYYY-MM-DDTHH:MM:SS
        assert "T" in meta["collected_at"]

    def test_category_default(self):
        """category 기본값은 'general'이다."""
        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        assert meta["category"] == "general"

    @patch("app.pipeline.metadata_builder.datetime")
    def test_collected_at_uses_current_time(self, mock_dt):
        """collected_at이 현재 시간을 사용한다."""
        from datetime import datetime

        fake_now = datetime(2025, 3, 10, 16, 35, 0)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        meta = build_news_metadata(self.SAMPLE_ITEM, "naver_news", "KOR")
        assert meta["collected_at"] == "2025-03-10T16:35:00"

    def test_category_from_item(self):
        """item에 category가 있으면 해당 값을 사용한다."""
        item = {**self.SAMPLE_ITEM, "category": "semiconductor"}
        meta = build_news_metadata(item, "naver_news", "KOR")
        assert meta["category"] == "semiconductor"

    def test_missing_pubdate_handled(self):
        """pubDate가 없는 항목도 처리한다."""
        item = {"title": "테스트", "link": "http://a"}
        meta = build_news_metadata(item, "test", "KOR")
        assert "published_at" in meta
