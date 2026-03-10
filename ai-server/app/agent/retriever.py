"""T-210: ChromaDB Retriever 설정.

ChromaDB에서 시장(market) 필터가 적용된 LangChain retriever를 생성한다.
"""

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


def get_retriever(chroma_host: str, chroma_port: int, market: str, k: int = 5):
    """ChromaDB에서 시장(market) 필터가 적용된 retriever를 반환한다.

    Args:
        chroma_host: ChromaDB 서버 호스트.
        chroma_port: ChromaDB 서버 포트.
        market: 시장 코드 (예: "KOR", "US").
        k: 검색할 문서 수 (기본값 5).

    Returns:
        LangChain VectorStoreRetriever 인스턴스.
    """
    collection_name = f"news_{market.lower()}"
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
    client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    vectorstore = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embedding_function,
    )

    return vectorstore.as_retriever(
        search_kwargs={"k": k, "filter": {"market": market}},
    )
