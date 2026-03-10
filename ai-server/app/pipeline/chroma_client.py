"""T-111: ChromaDB 클라이언트 초기화 모듈.

ChromaDB HttpClient 생성 및 컬렉션 조회/생성 기능을 제공한다.
"""

import chromadb


def get_chroma_client(host: str, port: int) -> chromadb.HttpClient:
    """ChromaDB HttpClient를 생성하여 반환한다.

    Args:
        host: ChromaDB 서버 호스트
        port: ChromaDB 서버 포트

    Returns:
        ChromaDB HttpClient 인스턴스
    """
    return chromadb.HttpClient(host=host, port=port)


def get_or_create_collection(client: chromadb.HttpClient, name: str):
    """컬렉션을 조회하거나 없으면 생성한다.

    Args:
        client: ChromaDB 클라이언트
        name: 컬렉션 이름

    Returns:
        ChromaDB Collection 객체

    Raises:
        ValueError: 컬렉션 이름이 비어있는 경우
    """
    if not name or not name.strip():
        msg = "collection name must not be empty"
        raise ValueError(msg)

    return client.get_or_create_collection(name=name)
