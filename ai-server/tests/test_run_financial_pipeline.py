"""run_financial_pipeline 통합 테스트 (T-506)."""

from unittest.mock import patch


class TestRunFinancialPipeline:
    """run_financial_pipeline() 통합 테스트."""

    CONFIG = {
        "supabase_url": "http://localhost:54321",
        "supabase_key": "test-key",
        "tickers": [("005930", "KOR"), ("AAPL", "US")],
    }

    @patch("app.pipeline.run_financial_pipeline.upsert_company_profiles", return_value=2)
    @patch("app.pipeline.run_financial_pipeline.upsert_financial_metrics", return_value=2)
    @patch(
        "app.pipeline.run_financial_pipeline.fetch_company_profile",
        return_value={"ticker": "X", "name": "Test"},
    )
    @patch(
        "app.pipeline.run_financial_pipeline.fetch_financial_metrics",
        return_value={"ticker": "X", "period": "2025Q1", "per": 10},
    )
    def test_normal_run(self, mock_fetch_m, mock_fetch_p, mock_upsert_m, mock_upsert_p):
        from app.pipeline.run_financial_pipeline import run_financial_pipeline

        result = run_financial_pipeline(self.CONFIG)

        assert result["metrics_collected"] == 2
        assert result["profiles_collected"] == 2
        assert result["metrics_upserted"] == 2
        assert result["profiles_upserted"] == 2

    @patch("app.pipeline.run_financial_pipeline.upsert_company_profiles", return_value=0)
    @patch("app.pipeline.run_financial_pipeline.upsert_financial_metrics", return_value=0)
    @patch("app.pipeline.run_financial_pipeline.fetch_company_profile", return_value=None)
    @patch("app.pipeline.run_financial_pipeline.fetch_financial_metrics", return_value=None)
    def test_all_failures(self, mock_fetch_m, mock_fetch_p, mock_upsert_m, mock_upsert_p):
        from app.pipeline.run_financial_pipeline import run_financial_pipeline

        result = run_financial_pipeline(self.CONFIG)

        assert result["metrics_collected"] == 0
        assert result["profiles_collected"] == 0
        # upsert should not be called when no data collected
        mock_upsert_m.assert_not_called()
        mock_upsert_p.assert_not_called()

    @patch("app.pipeline.run_financial_pipeline.upsert_company_profiles", return_value=1)
    @patch("app.pipeline.run_financial_pipeline.upsert_financial_metrics", return_value=1)
    @patch(
        "app.pipeline.run_financial_pipeline.fetch_company_profile",
        side_effect=[None, {"ticker": "AAPL", "name": "Apple"}],
    )
    @patch(
        "app.pipeline.run_financial_pipeline.fetch_financial_metrics",
        side_effect=[{"ticker": "005930", "period": "2025Q1", "per": 10}, None],
    )
    def test_partial_success(self, mock_fetch_m, mock_fetch_p, mock_upsert_m, mock_upsert_p):
        from app.pipeline.run_financial_pipeline import run_financial_pipeline

        result = run_financial_pipeline(self.CONFIG)

        assert result["metrics_collected"] == 1
        assert result["profiles_collected"] == 1
        assert result["metrics_upserted"] == 1
        assert result["profiles_upserted"] == 1
