"""T-114: ChromaDB upsert 모듈.

청크 데이터를 ChromaDB에 upsert하고 컬렉션 상태를 조회한다.
"""

import logging

logger = logging.getLogger(__name__)


def upsert_chunks(collection, chunks: list[dict]) -> int:
    """청크 리스트를 ChromaDB 컬렉션에 upsert한다.

    id 기반 멱등성을 보장하여 같은 id면 덮어쓴다.

    Args:
        collection: ChromaDB Collection 객체
        chunks: [{"id": str, "document": str, "metadata": dict, "embedding": list[float]}]

    Returns:
        upsert된 문서 수
    """
    if not chunks:
        return 0

    ids = [c["id"] for c in chunks]
    documents = [c["document"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    embeddings = [c["embedding"] for c in chunks]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return len(chunks)


def get_collection_count(collection) -> int:
    """컬렉션 내 문서 수를 반환한다.

    Args:
        collection: ChromaDB Collection 객체

    Returns:
        문서 수
    """
    return collection.count()
