"""T-105: OpenDart API 기업 공시 수집 모듈 테스트."""

from unittest.mock import MagicMock, patch

from app.pipeline.dart_collector import fetch_dart_disclosures


class TestFetchDartDisclosures:
    """fetch_dart_disclosures 함수 테스트 스위트."""

    SAMPLE_RESPONSE = {
        "status": "000",
        "message": "정상",
        "list": [
            {
                "corp_name": "삼성전자",
                "report_nm": "사업보고서 (2024.12)",
                "rcept_dt": "20250310",
                "flr_nm": "삼성전자",
                "rcept_no": "20250310000001",
            },
            {
                "corp_name": "SK하이닉스",
                "report_nm": "분기보고서 (2025.03)",
                "rcept_dt": "20250310",
                "flr_nm": "SK하이닉스",
                "rcept_no": "20250310000002",
            },
        ],
    }

    # ------------------------------------------------------------------ #
    # 정상 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_disclosure_list(self, mock_get):
        """정상 응답 시 공시 목록을 dict 리스트로 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("test_api_key", "20250310")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["corp_name"] == "삼성전자"
        assert result[0]["report_nm"] == "사업보고서 (2024.12)"
        assert result[0]["rcept_dt"] == "20250310"

    @patch("app.pipeline.dart_collector.requests.get")
    def test_passes_correct_params_to_api(self, mock_get):
        """API에 올바른 파라미터가 전달된다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "013", "message": "조회된 데이터가 없습니다."}
        mock_get.return_value = mock_resp

        fetch_dart_disclosures("my_key", "20250310")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["crtfc_key"] == "my_key"
        assert params["bgn_de"] == "20250310"
        assert params["end_de"] == "20250310"

    @patch("app.pipeline.dart_collector.requests.get")
    def test_includes_title_field(self, mock_get):
        """반환 dict에 title 필드가 포함된다 (report_nm 매핑)."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self.SAMPLE_RESPONSE
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("key", "20250310")

        for item in result:
            assert "title" in item
            assert "corp_name" in item
            assert "rcept_dt" in item
            assert "report_nm" in item

    # ------------------------------------------------------------------ #
    # 빈 응답 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_empty_list_when_no_data(self, mock_get):
        """status=013 (데이터 없음) 시 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "013",
            "message": "조회된 데이터가 없습니다.",
        }
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("key", "20250310")

        assert result == []

    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_empty_list_when_list_key_missing(self, mock_get):
        """응답에 list 키가 없으면 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "000", "message": "정상"}
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("key", "20250310")

        assert result == []

    # ------------------------------------------------------------------ #
    # API 오류 / 예외 처리
    # ------------------------------------------------------------------ #
    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_empty_list_on_http_error(self, mock_get):
        """HTTP 오류 응답 시 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("Server Error")
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("key", "20250310")

        assert result == []

    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_empty_list_on_network_error(self, mock_get):
        """네트워크 예외 발생 시 빈 리스트를 반환한다."""
        mock_get.side_effect = Exception("Connection refused")

        result = fetch_dart_disclosures("key", "20250310")

        assert result == []

    @patch("app.pipeline.dart_collector.requests.get")
    def test_returns_empty_list_on_invalid_json(self, mock_get):
        """JSON 파싱 실패 시 빈 리스트를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_resp

        result = fetch_dart_disclosures("key", "20250310")

        assert result == []
