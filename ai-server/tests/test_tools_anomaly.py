"""T-223: price_anomaly_tool 테스트 -- Z-score 이상 감지."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")

from unittest.mock import patch

import pandas as pd


class TestCalculateZscore:
    """calculate_zscore 순수 함수 단위 테스트 (100% 커버리지 목표)."""

    def test_known_data_zscore(self):
        """알려진 데이터로 Z-score 정확도를 검증한다."""
        from app.agent.tools import calculate_zscore

        # [1, 2, 3, 4, 10] -> mean=4.0, std=3.162..., z=(10-4)/3.162 = 1.897
        returns = [1.0, 2.0, 3.0, 4.0, 10.0]
        z = calculate_zscore(returns)
        assert z is not None
        assert abs(z - 1.897) < 0.01

    def test_identical_values_returns_zero(self):
        """모든 값이 동일하면 Z-score는 0 (또는 None 표준편차 0)."""
        from app.agent.tools import calculate_zscore

        returns = [5.0, 5.0, 5.0, 5.0, 5.0]
        z = calculate_zscore(returns)
        # 표준편차가 0이면 Z-score는 계산 불가 -> None 반환
        assert z is None

    def test_returns_none_for_insufficient_data(self):
        """데이터가 5개 미만이면 None을 반환한다."""
        from app.agent.tools import calculate_zscore

        assert calculate_zscore([1.0, 2.0, 3.0, 4.0]) is None
        assert calculate_zscore([1.0]) is None
        assert calculate_zscore([]) is None

    def test_negative_zscore(self):
        """음수 Z-score를 정확히 계산한다."""
        from app.agent.tools import calculate_zscore

        # [10, 9, 8, 7, 1] -> mean=7.0, std=3.162..., z=(1-7)/3.162 = -1.897
        returns = [10.0, 9.0, 8.0, 7.0, 1.0]
        z = calculate_zscore(returns)
        assert z is not None
        assert abs(z - (-1.897)) < 0.01

    def test_detects_anomaly_above_threshold(self):
        """|Z-score| > 2 이상인 경우를 감지한다."""
        from app.agent.tools import calculate_zscore

        # 정상 범위: [0.01, 0.01, 0.01, 0.01, ...], 마지막에 0.10 (큰 이탈)
        returns = [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.10]
        z = calculate_zscore(returns)
        assert z is not None
        assert abs(z) > 2.0

    def test_exact_five_data_points(self):
        """정확히 5개 데이터도 계산할 수 있다."""
        from app.agent.tools import calculate_zscore

        returns = [1.0, 2.0, 3.0, 4.0, 5.0]
        z = calculate_zscore(returns)
        assert z is not None

    def test_with_all_negative_returns(self):
        """모두 음수인 수익률도 정확히 계산한다."""
        from app.agent.tools import calculate_zscore

        returns = [-0.01, -0.02, -0.03, -0.02, -0.10]
        z = calculate_zscore(returns)
        assert z is not None
        assert z < 0  # 마지막 값이 평균보다 크게 아래이므로 음수


class TestDetectPriceAnomaly:
    """detect_price_anomaly 함수 단위 테스트."""

    @patch("app.agent.tools.fdr.DataReader")
    def test_returns_anomaly_message_when_detected(self, mock_datareader):
        """Z-score > 2 이상이면 이상 감지 메시지를 반환한다."""
        from app.agent.tools import detect_price_anomaly

        # 일반적 가격 + 급등
        prices = [100] * 19 + [150]
        dates = pd.date_range("2025-01-01", periods=20)
        df = pd.DataFrame({"Close": prices}, index=dates)
        mock_datareader.return_value = df

        result = detect_price_anomaly("005930")

        assert "이상" in result or "급등" in result or "급락" in result or "Z-score" in result

    @patch("app.agent.tools.fdr.DataReader")
    def test_returns_normal_when_no_anomaly(self, mock_datareader):
        """Z-score가 정상 범위이면 정상 메시지를 반환한다."""
        from app.agent.tools import detect_price_anomaly

        # 점진적 상승 (이상 없음)
        prices = list(range(100, 120))
        dates = pd.date_range("2025-01-01", periods=20)
        df = pd.DataFrame({"Close": prices}, index=dates)
        mock_datareader.return_value = df

        result = detect_price_anomaly("005930")

        assert "정상" in result or "이상 없" in result or "특이" in result

    @patch("app.agent.tools.fdr.DataReader")
    def test_handles_insufficient_data(self, mock_datareader):
        """데이터가 부족하면 (< 5일) 적절한 메시지를 반환한다."""
        from app.agent.tools import detect_price_anomaly

        prices = [100, 101, 102]
        dates = pd.date_range("2025-01-01", periods=3)
        df = pd.DataFrame({"Close": prices}, index=dates)
        mock_datareader.return_value = df

        result = detect_price_anomaly("005930")

        assert "부족" in result or "충분하지" in result or "데이터" in result

    @patch("app.agent.tools.fdr.DataReader")
    def test_handles_datareader_exception(self, mock_datareader):
        """FinanceDataReader 오류 시 에러 메시지를 반환한다."""
        from app.agent.tools import detect_price_anomaly

        mock_datareader.side_effect = Exception("Network error")

        result = detect_price_anomaly("INVALID")

        assert "오류" in result or "실패" in result

    @patch("app.agent.tools.fdr.DataReader")
    def test_handles_empty_dataframe(self, mock_datareader):
        """빈 DataFrame을 처리한다."""
        from app.agent.tools import detect_price_anomaly

        mock_datareader.return_value = pd.DataFrame()

        result = detect_price_anomaly("005930")

        assert "부족" in result or "데이터" in result or "오류" in result

    @patch("app.agent.tools.fdr.DataReader")
    def test_includes_zscore_value_in_result(self, mock_datareader):
        """결과에 Z-score 값이 포함된다."""
        from app.agent.tools import detect_price_anomaly

        prices = [100] * 19 + [150]
        dates = pd.date_range("2025-01-01", periods=20)
        df = pd.DataFrame({"Close": prices}, index=dates)
        mock_datareader.return_value = df

        result = detect_price_anomaly("005930")

        assert "Z-score" in result or "z-score" in result.lower()
