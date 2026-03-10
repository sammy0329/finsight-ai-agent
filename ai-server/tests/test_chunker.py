"""T-112: 청킹 모듈 테스트."""

from app.pipeline.chunker import chunk_news_item, chunk_text


# ================================================================== #
# chunk_text
# ================================================================== #
class TestChunkText:
    """텍스트 청킹 테스트 (RecursiveCharacterTextSplitter 사용)."""

    def test_short_text_single_chunk(self):
        """chunk_size보다 짧은 텍스트는 하나의 청크를 반환한다."""
        text = "짧은 텍스트입니다."
        result = chunk_text(text, chunk_size=500, chunk_overlap=50)

        assert len(result) == 1
        assert result[0] == text

    def test_long_text_multiple_chunks(self):
        """chunk_size보다 긴 텍스트는 여러 청크로 분할된다."""
        text = "가나다라마바사. " * 100  # 약 900자
        result = chunk_text(text, chunk_size=100, chunk_overlap=10)

        assert len(result) > 1
        # 각 청크가 chunk_size를 크게 초과하지 않아야 한다
        for chunk in result:
            assert len(chunk) <= 200  # 여유 있는 상한

    def test_empty_text_returns_empty_list(self):
        """빈 문자열이면 빈 리스트를 반환한다."""
        result = chunk_text("", chunk_size=500, chunk_overlap=50)

        assert result == []

    def test_whitespace_only_returns_empty_list(self):
        """공백만 있는 문자열이면 빈 리스트를 반환한다."""
        result = chunk_text("   \n\t  ", chunk_size=500, chunk_overlap=50)

        assert result == []

    def test_overlap_creates_overlapping_content(self):
        """overlap이 있으면 청크 간에 중복 내용이 존재한다."""
        # 문장 단위로 구분 가능하도록 구성
        sentences = [f"문장번호{i}입니다." for i in range(50)]
        text = " ".join(sentences)
        result = chunk_text(text, chunk_size=100, chunk_overlap=30)

        if len(result) >= 2:
            # 인접 청크 간에 공통 부분이 있어야 함
            found_overlap = False
            for i in range(len(result) - 1):
                if any(word in result[i + 1] for word in result[i].split()[-3:]):
                    found_overlap = True
                    break
            assert found_overlap, "인접 청크 간 overlap이 존재해야 한다"

    def test_default_parameters(self):
        """기본 파라미터(chunk_size=500, chunk_overlap=50)로 동작한다."""
        text = "테스트. " * 200
        result = chunk_text(text)

        assert len(result) >= 1
        assert isinstance(result, list)
        assert all(isinstance(c, str) for c in result)

    def test_all_chunks_are_strings(self):
        """반환된 모든 청크가 문자열이다."""
        text = "Hello world. " * 100
        result = chunk_text(text, chunk_size=50, chunk_overlap=5)

        assert all(isinstance(chunk, str) for chunk in result)


# ================================================================== #
# chunk_news_item
# ================================================================== #
class TestChunkNewsItem:
    """뉴스 1건 청킹 테스트."""

    def test_returns_list_of_chunk_dicts(self):
        """뉴스 1건을 청킹하면 dict 리스트를 반환한다."""
        item = {"title": "테스트 뉴스", "description": "설명입니다. " * 50}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": ["005930"],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        assert len(result) >= 1
        for chunk in result:
            assert "document" in chunk
            assert "metadata" in chunk
            assert "id" in chunk

    def test_chunk_id_format(self):
        """청크 id는 source_hash 형태이다."""
        item = {"title": "뉴스", "description": "내용"}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        for chunk in result:
            assert chunk["id"].startswith("naver_news_")

    def test_metadata_attached_to_each_chunk(self):
        """각 청크에 원본 메타데이터가 포함된다."""
        item = {"title": "뉴스 제목", "description": "뉴스 본문 " * 100}
        metadata = {
            "source": "newsapi",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "US",
            "related_tickers": ["AAPL"],
            "category": "general",
            "sentiment": "positive",
        }

        result = chunk_news_item(item, metadata)

        for chunk in result:
            assert chunk["metadata"]["source"] == "newsapi"
            assert chunk["metadata"]["market"] == "US"

    def test_empty_description_uses_title_only(self):
        """description이 비어있으면 title만으로 청킹한다."""
        item = {"title": "뉴스 제목만 있음", "description": ""}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        assert len(result) >= 1
        assert "뉴스 제목만 있음" in result[0]["document"]

    def test_empty_item_returns_empty_list(self):
        """title과 description 모두 비어있으면 빈 리스트를 반환한다."""
        item = {"title": "", "description": ""}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        assert result == []

    def test_chunk_metadata_includes_chunk_index(self):
        """각 청크 메타데이터에 chunk_index가 포함된다."""
        item = {"title": "뉴스", "description": "내용이 길다. " * 200}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        if len(result) > 1:
            for i, chunk in enumerate(result):
                assert chunk["metadata"]["chunk_index"] == i

    def test_unique_ids_per_chunk(self):
        """동일 뉴스의 청크들은 서로 다른 id를 가진다."""
        item = {"title": "뉴스", "description": "내용이 서로 다르다. " * 200}
        metadata = {
            "source": "naver_news",
            "published_at": "2025-03-10",
            "collected_at": "2025-03-10T12:00:00",
            "market": "KOR",
            "related_tickers": [],
            "category": "general",
            "sentiment": "neutral",
        }

        result = chunk_news_item(item, metadata)

        ids = [chunk["id"] for chunk in result]
        assert len(ids) == len(set(ids)), "모든 청크 id가 고유해야 한다"
