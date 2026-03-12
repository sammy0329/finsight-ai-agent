"""T-609: 리포트 생성 파이프라인 테스트."""

from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# TestBuildMarketSection
# ---------------------------------------------------------------------------
class TestBuildMarketSection:
    """build_market_section() 테스트."""

    def test_kor_market_contains_kospi_kosdaq_fx(self):
        """KOR 지수(KOSPI, KOSDAQ)와 USD/KRW 환율을 포함한 market 섹션을 반환한다."""
        from app.pipeline.report_generator import build_market_section

        indices = [
            {"symbol": "KS11", "name": "KOSPI", "close": 2612.34, "change_pct": 0.8},
            {"symbol": "KQ11", "name": "KOSDAQ", "close": 768.12, "change_pct": 1.2},
        ]
        fx_rates = [{"pair": "USD/KRW", "rate": 1325.0}]

        result = build_market_section(indices, fx_rates)

        assert "kospi" in result
        assert result["kospi"]["value"] == 2612.34
        assert result["kospi"]["change_pct"] == 0.8
        assert "kosdaq" in result
        assert result["usdkrw"] == 1325.0

    def test_us_market_contains_sp500_nasdaq_dow(self):
        """US 지수(S&P500, NASDAQ, DOW)를 포함한 market 섹션을 반환한다."""
        from app.pipeline.report_generator import build_market_section

        indices = [
            {"symbol": "GSPC", "name": "S&P500", "close": 5200.50, "change_pct": 0.5},
            {"symbol": "IXIC", "name": "NASDAQ", "close": 16400.0, "change_pct": 0.7},
            {"symbol": "DJI", "name": "DOW", "close": 39000.0, "change_pct": 0.3},
        ]
        fx_rates = []

        result = build_market_section(indices, fx_rates)

        assert "sp500" in result
        assert result["sp500"]["value"] == 5200.50
        assert "nasdaq" in result
        assert "dow" in result

    def test_empty_inputs_returns_empty_dict(self):
        """입력 데이터가 없으면 빈 dict를 반환한다."""
        from app.pipeline.report_generator import build_market_section

        result = build_market_section([], [])

        assert result == {}


# ---------------------------------------------------------------------------
# TestBuildStocksSection
# ---------------------------------------------------------------------------
class TestBuildStocksSection:
    """build_stocks_section() 테스트."""

    PRICES = [
        {"ticker": "005930", "name": "삼성전자", "close": 73400.0, "change_pct": 3.2},
    ]
    SECTORS = {"005930": "반도체"}
    ANOMALIES = {
        "005930": {"zscore": 2.4, "is_anomaly": True},
    }
    NEWS_SUMMARIES = {"005930": "HBM 수주 확대 기대감 상승"}

    def test_combines_all_fields(self):
        """가격·섹터·이상감지·뉴스요약을 하나의 stocks 항목으로 통합한다."""
        from app.pipeline.report_generator import build_stocks_section

        result = build_stocks_section(
            self.PRICES, self.SECTORS, self.ANOMALIES, self.NEWS_SUMMARIES
        )

        assert len(result) == 1
        stock = result[0]
        assert stock["ticker"] == "005930"
        assert stock["name"] == "삼성전자"
        assert stock["sector"] == "반도체"
        assert stock["close"] == 73400.0
        assert stock["change_pct"] == 3.2
        assert stock["zscore"] == 2.4
        assert stock["price_anomaly"] is True
        assert stock["news_summary"] == "HBM 수주 확대 기대감 상승"

    def test_missing_anomaly_defaults_to_false(self):
        """이상감지 데이터가 없으면 zscore=None, price_anomaly=False로 설정한다."""
        from app.pipeline.report_generator import build_stocks_section

        result = build_stocks_section(self.PRICES, self.SECTORS, {}, {})

        stock = result[0]
        assert stock["zscore"] is None
        assert stock["price_anomaly"] is False
        assert stock["news_summary"] == ""

    def test_empty_prices_returns_empty_list(self):
        """가격 데이터가 없으면 빈 리스트를 반환한다."""
        from app.pipeline.report_generator import build_stocks_section

        result = build_stocks_section([], {}, {}, {})

        assert result == []


# ---------------------------------------------------------------------------
# TestSummarizeMarketNews
# ---------------------------------------------------------------------------
class TestSummarizeMarketNews:
    """summarize_market_news() 테스트."""

    @patch("app.pipeline.report_generator.OpenAI")
    def test_returns_llm_summary(self, mock_openai_cls):
        """OpenAI 응답을 그대로 반환한다."""
        from app.pipeline.report_generator import summarize_market_news

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[
            0
        ].message.content = "오늘 시장 요약입니다."

        result = summarize_market_news(
            news_texts=["뉴스1", "뉴스2"],
            report_label="한국 장 마감 리포트",
            openai_key="test-key",
        )

        assert result == "오늘 시장 요약입니다."
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.pipeline.report_generator.OpenAI")
    def test_returns_fallback_on_error(self, mock_openai_cls):
        """OpenAI 오류 시 폴백 메시지를 반환한다."""
        from app.pipeline.report_generator import summarize_market_news

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        result = summarize_market_news(
            news_texts=["뉴스1"],
            report_label="한국 장 마감 리포트",
            openai_key="test-key",
        )

        assert isinstance(result, str)
        assert len(result) > 0  # 빈 문자열이 아닌 폴백 메시지


# ---------------------------------------------------------------------------
# TestFetchLatestIndices
# ---------------------------------------------------------------------------
class TestFetchLatestIndices:
    """fetch_latest_indices() 테스트."""

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_indices_for_market(self, mock_create_client):
        """Supabase에서 해당 market의 최근 지수 데이터를 반환한다."""
        from app.pipeline.report_generator import fetch_latest_indices

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value.data = [
            {"symbol": "KS11", "name": "KOSPI", "close": 2612.0, "change_pct": 0.8, "market": "KOR"}
        ]

        result = fetch_latest_indices("http://test", "key", "KOR", "2026-03-12")

        assert len(result) == 1
        assert result[0]["symbol"] == "KS11"

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_empty_on_error(self, mock_create_client):
        """Supabase 오류 시 빈 리스트를 반환한다."""
        from app.pipeline.report_generator import fetch_latest_indices

        mock_create_client.side_effect = Exception("Connection error")

        result = fetch_latest_indices("http://test", "key", "KOR", "2026-03-12")

        assert result == []


# ---------------------------------------------------------------------------
# TestGetWatchlistUserIds
# ---------------------------------------------------------------------------
class TestGetWatchlistUserIds:
    """get_watchlist_user_ids() 테스트."""

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_unique_user_ids(self, mock_create_client):
        """watchlist에서 해당 market 종목을 가진 고유 사용자 UUID 목록을 반환한다."""
        from app.pipeline.report_generator import get_watchlist_user_ids

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"user_id": "uuid-1"},
            {"user_id": "uuid-2"},
            {"user_id": "uuid-1"},  # 중복
        ]

        result = get_watchlist_user_ids("http://test", "key", "KOR")

        assert sorted(result) == ["uuid-1", "uuid-2"]

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_empty_on_error(self, mock_create_client):
        """오류 시 빈 리스트를 반환한다."""
        from app.pipeline.report_generator import get_watchlist_user_ids

        mock_create_client.side_effect = Exception("DB Error")

        result = get_watchlist_user_ids("http://test", "key", "KOR")

        assert result == []


# ---------------------------------------------------------------------------
# TestInsertNotifications
# ---------------------------------------------------------------------------
class TestInsertNotifications:
    """insert_notifications() 테스트."""

    SAMPLE_PAYLOAD = {"market_summary": "요약", "market": {}, "stocks": [], "top_news": []}

    @patch("app.pipeline.report_generator.create_client")
    def test_inserts_one_per_user(self, mock_create_client):
        """사용자 수만큼 알림 row를 삽입한다."""
        from app.pipeline.report_generator import insert_notifications

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "notif-1"},
            {"id": "notif-2"},
        ]

        result = insert_notifications(
            "KOR_CLOSE", self.SAMPLE_PAYLOAD, ["uuid-1", "uuid-2"], "http://test", "key"
        )

        assert result == 2
        # insert 호출 시 2개 row 전달됐는지 확인
        call_args = mock_client.table.return_value.insert.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["report_type"] == "KOR_CLOSE"
        assert call_args[0]["user_id"] == "uuid-1"

    def test_skips_insert_on_empty_user_list(self):
        """사용자 목록이 비어 있으면 insert를 호출하지 않고 0을 반환한다."""
        from app.pipeline.report_generator import insert_notifications

        result = insert_notifications("KOR_CLOSE", self.SAMPLE_PAYLOAD, [], "http://test", "key")

        assert result == 0

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_zero_on_error(self, mock_create_client):
        """insert 오류 시 0을 반환한다."""
        from app.pipeline.report_generator import insert_notifications

        mock_create_client.side_effect = Exception("DB Error")

        result = insert_notifications(
            "KOR_CLOSE", self.SAMPLE_PAYLOAD, ["uuid-1"], "http://test", "key"
        )

        assert result == 0


# ---------------------------------------------------------------------------
# TestUpsertSnapshot
# ---------------------------------------------------------------------------
class TestUpsertSnapshot:
    """upsert_snapshot() 테스트."""

    SAMPLE_PAYLOAD = {"market_summary": "요약", "market": {}, "stocks": [], "top_news": []}

    @patch("app.pipeline.report_generator.create_client")
    def test_upserts_and_returns_id(self, mock_create_client):
        """market_snapshots에 upsert하고 snapshot id를 반환한다."""
        from app.pipeline.report_generator import upsert_snapshot

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
            {"id": "snapshot-uuid-1"}
        ]

        result = upsert_snapshot(
            "KOR_CLOSE", "2026-03-13", self.SAMPLE_PAYLOAD, "http://test", "key"
        )

        assert result == "snapshot-uuid-1"

    @patch("app.pipeline.report_generator.create_client")
    def test_returns_none_on_error(self, mock_create_client):
        """오류 시 None을 반환한다."""
        from app.pipeline.report_generator import upsert_snapshot

        mock_create_client.side_effect = Exception("DB Error")

        result = upsert_snapshot(
            "KOR_CLOSE", "2026-03-13", self.SAMPLE_PAYLOAD, "http://test", "key"
        )

        assert result is None


# ---------------------------------------------------------------------------
# TestRunReportPipeline
# ---------------------------------------------------------------------------
class TestRunReportPipeline:
    """run_report_pipeline() 통합 테스트."""

    CONFIG = {
        "supabase_url": "http://test",
        "supabase_key": "key",
        "openai_api_key": "openai-key",
        "chroma_host": "localhost",
        "chroma_port": 8001,
        "date": "2026-03-13",
    }

    @patch("app.pipeline.report_generator.insert_notifications", return_value=2)
    @patch("app.pipeline.report_generator.upsert_snapshot", return_value="snap-1")
    @patch("app.pipeline.report_generator.get_watchlist_user_ids", return_value=["u1", "u2"])
    @patch(
        "app.pipeline.report_generator.build_payload",
        return_value={"market_summary": "요약", "market": {}, "stocks": [], "top_news": []},
    )
    def test_kor_close_full_success(self, mock_payload, mock_users, mock_snap, mock_notif):
        """KOR_CLOSE 리포트 파이프라인 전체 성공 흐름을 테스트한다."""
        from app.pipeline.report_generator import run_report_pipeline

        result = run_report_pipeline("KOR_CLOSE", self.CONFIG)

        assert result["snapshot_id"] == "snap-1"
        assert result["notifications_inserted"] == 2
        assert result["report_type"] == "KOR_CLOSE"
        mock_payload.assert_called_once()
        mock_users.assert_called_once()
        mock_snap.assert_called_once()
        mock_notif.assert_called_once()

    @patch("app.pipeline.report_generator.insert_notifications", return_value=0)
    @patch("app.pipeline.report_generator.upsert_snapshot", return_value="snap-2")
    @patch("app.pipeline.report_generator.get_watchlist_user_ids", return_value=[])
    @patch(
        "app.pipeline.report_generator.build_payload",
        return_value={"market_summary": "요약", "market": {}, "stocks": [], "top_news": []},
    )
    def test_no_watchlist_users_inserts_zero_notifications(
        self, mock_payload, mock_users, mock_snap, mock_notif
    ):
        """watchlist 사용자가 없으면 알림이 0건 삽입된다."""
        from app.pipeline.report_generator import run_report_pipeline

        result = run_report_pipeline("US_CLOSE", self.CONFIG)

        assert result["notifications_inserted"] == 0
        mock_notif.assert_not_called()

    @patch("app.pipeline.report_generator.build_payload", side_effect=Exception("LLM Error"))
    def test_payload_build_error_returns_failure(self, mock_payload):
        """payload 빌드 오류 시 success=False를 반환한다."""
        from app.pipeline.report_generator import run_report_pipeline

        result = run_report_pipeline("KOR_PREMARKET", self.CONFIG)

        assert result["success"] is False
        assert "error" in result
