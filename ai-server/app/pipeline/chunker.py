"""T-112: 청킹 모듈.

텍스트를 일정 크기의 청크로 분할하고, 뉴스 항목을 청킹하여 메타데이터와 함께 반환한다.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """텍스트를 RecursiveCharacterTextSplitter로 청킹한다.

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 최대 크기 (문자 수)
        chunk_overlap: 청크 간 겹침 크기 (문자 수)

    Returns:
        청크 문자열 리스트. 빈 텍스트이면 빈 리스트 반환.
    """
    if not text or not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)


def chunk_news_item(item: dict, metadata: dict) -> list[dict]:
    """뉴스 1건을 청킹하여 문서/메타데이터/ID를 포함하는 dict 리스트를 반환한다.

    Args:
        item: 뉴스 딕셔너리 (title, description 등)
        metadata: 부착할 메타데이터

    Returns:
        [{"document": str, "metadata": dict, "id": str}] 형태의 리스트.
        title과 description 모두 비어있으면 빈 리스트 반환.
    """
    title = item.get("title", "")
    description = item.get("description", "")

    # title과 description을 결합
    parts = [p for p in [title, description] if p and p.strip()]
    if not parts:
        return []

    full_text = "\n".join(parts)
    chunks = chunk_text(full_text)

    result = []
    for i, doc in enumerate(chunks):
        chunk_id = f"{metadata['source']}_{hash(doc)}_{i}"
        chunk_metadata = {**metadata, "chunk_index": i}
        result.append(
            {
                "document": doc,
                "metadata": chunk_metadata,
                "id": chunk_id,
            }
        )
    return result
