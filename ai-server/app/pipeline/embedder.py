"""T-113: 임베딩 모듈.

OpenAI text-embedding-3-small 모델을 사용하여 텍스트를 벡터로 변환한다.
"""

import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def embed_documents(texts: list[str], api_key: str) -> list[list[float]]:
    """텍스트 리스트를 OpenAI 임베딩 벡터로 변환한다.

    100개 단위로 배치 처리하여 API를 호출한다.

    Args:
        texts: 임베딩할 텍스트 리스트
        api_key: OpenAI API 키

    Returns:
        임베딩 벡터 리스트 (각 벡터는 float 리스트)
    """
    if not texts:
        return []

    client = OpenAI(api_key=api_key)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        response = client.embeddings.create(
            input=batch,
            model="text-embedding-3-small",
        )
        for item in response.data:
            all_embeddings.append(item.embedding)

    return all_embeddings
