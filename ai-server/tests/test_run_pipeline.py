"""T-115: 파이프라인 통합 실행 스크립트 테스트."""

from unittest.mock import MagicMock, patch

from app.pipeline.run_pipeline import run_pipeline


def _base_config():
    """테스트용 기본 config를 반환한다."""
    return {
        "market": "KOR",
        "date": "2025-03-10",
        "tickers": ["005930"],
        "openai_api_key": "test-key",
        "naver_client_id": "test-naver-id",
        "naver_client_secret": "test-naver-secret",
        "news_api_key": "test-news-api-key",
        "chroma_host": "localhost",
        "chroma_port": 8000,
    }


# ================================================================== #
# run_pipeline - 정상 흐름
# ================================================================== #
class TestRunPipelineSuccess:
    """파이프라인 정상 실행 테스트."""

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_returns_stats_dict(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """정상 실행 시 collected, cleaned, chunked, upserted 통계를 반환한다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()

        # 수집: 3건
        mock_fetch_news_multi.return_value = [
            {"title": "뉴스1", "description": "내용1", "link": "http://a", "pubDate": "2025"},
            {"title": "뉴스2", "description": "내용2", "link": "http://b", "pubDate": "2025"},
            {"title": "뉴스3", "description": "내용3", "link": "http://c", "pubDate": "2025"},
        ]
        # 정제: 2건
        mock_clean.return_value = [
            {"title": "뉴스1", "description": "내용1", "link": "http://a", "pubDate": "2025"},
            {"title": "뉴스2", "description": "내용2", "link": "http://b", "pubDate": "2025"},
        ]
        # 메타데이터
        mock_metadata.return_value = {
            "source": "naver_news",
            "published_at": "2025",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }
        # 청킹: 각 뉴스에서 2개 청크씩 -> 4개
        mock_chunk.return_value = [
            {"id": "id1", "document": "청크1", "metadata": {}},
            {"id": "id2", "document": "청크2", "metadata": {}},
        ]
        # 임베딩
        mock_embed.return_value = [[0.1, 0.2], [0.3, 0.4], [0.1, 0.2], [0.3, 0.4]]
        # upsert
        mock_upsert.return_value = 4

        result = run_pipeline(_base_config())

        assert result["collected"] == 3
        assert result["cleaned"] == 2
        assert result["chunked"] == 4
        assert result["upserted"] == 4

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_all_stats_keys_present(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """반환 dict에 필수 키가 모두 존재한다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()
        mock_fetch_news_multi.return_value = []
        mock_clean.return_value = []
        mock_embed.return_value = []
        mock_upsert.return_value = 0

        result = run_pipeline(_base_config())

        assert "collected" in result
        assert "cleaned" in result
        assert "chunked" in result
        assert "upserted" in result
        assert "deduplicated" in result


# ================================================================== #
# run_pipeline - 빈 데이터
# ================================================================== #
class TestRunPipelineEmpty:
    """수집 결과가 비어있는 경우 테스트."""

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_no_news_collected(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """뉴스가 0건 수집되면 모든 통계가 0이다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()
        mock_fetch_news_multi.return_value = []
        mock_clean.return_value = []

        result = run_pipeline(_base_config())

        assert result["collected"] == 0
        assert result["cleaned"] == 0
        assert result["chunked"] == 0
        assert result["upserted"] == 0


# ================================================================== #
# run_pipeline - 오류 복구
# ================================================================== #
class TestRunPipelineErrorRecovery:
    """각 단계 실패 시 파이프라인이 중단되지 않는 테스트."""

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_collector_failure_returns_zeros(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """수집 단계 실패 시 로그 기록 후 0 통계를 반환한다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()
        mock_fetch_news_multi.side_effect = Exception("Network error")

        result = run_pipeline(_base_config())

        assert result["collected"] == 0
        assert result["cleaned"] == 0
        assert result["chunked"] == 0
        assert result["upserted"] == 0

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_embed_failure_does_not_crash(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """임베딩 단계 실패 시 파이프라인이 중단되지 않는다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()
        mock_fetch_news_multi.return_value = [
            {"title": "뉴스", "description": "내용", "link": "http://a", "pubDate": "2025"},
        ]
        mock_clean.return_value = [
            {"title": "뉴스", "description": "내용", "link": "http://a", "pubDate": "2025"},
        ]
        mock_metadata.return_value = {
            "source": "naver_news",
            "published_at": "2025",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }
        mock_chunk.return_value = [
            {"id": "id1", "document": "청크1", "metadata": {}},
        ]
        mock_embed.side_effect = RuntimeError("OpenAI API error")

        result = run_pipeline(_base_config())

        assert result["collected"] == 1
        assert result["cleaned"] == 1
        assert result["chunked"] == 1
        assert result["upserted"] == 0

    @patch("app.pipeline.run_pipeline.upsert_chunks")
    @patch("app.pipeline.run_pipeline.embed_documents")
    @patch("app.pipeline.run_pipeline.chunk_news_item")
    @patch("app.pipeline.run_pipeline.build_news_metadata")
    @patch("app.pipeline.run_pipeline.clean_news_items")
    @patch("app.pipeline.run_pipeline.fetch_naver_news_multi")
    @patch("app.pipeline.run_pipeline.get_or_create_collection")
    @patch("app.pipeline.run_pipeline.get_chroma_client")
    def test_upsert_failure_does_not_crash(
        self,
        mock_chroma_client,
        mock_get_collection,
        mock_fetch_news_multi,
        mock_clean,
        mock_metadata,
        mock_chunk,
        mock_embed,
        mock_upsert,
    ):
        """upsert 단계 실패 시 파이프라인이 중단되지 않는다."""
        mock_chroma_client.return_value = MagicMock()
        mock_get_collection.return_value = MagicMock()
        mock_fetch_news_multi.return_value = [
            {"title": "뉴스", "description": "내용", "link": "http://a", "pubDate": "2025"},
        ]
        mock_clean.return_value = [
            {"title": "뉴스", "description": "내용", "link": "http://a", "pubDate": "2025"},
        ]
        mock_metadata.return_value = {
            "source": "naver_news",
            "published_at": "2025",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }
        mock_chunk.return_value = [
            {"id": "id1", "document": "청크1", "metadata": {}},
        ]
        mock_embed.return_value = [[0.1, 0.2]]
        mock_upsert.side_effect = RuntimeError("ChromaDB error")

        result = run_pipeline(_base_config())

        assert result["collected"] == 1
        assert result["cleaned"] == 1
        assert result["chunked"] == 1
        assert result["upserted"] == 0
