"""T-203: 내부 서비스 인증 미들웨어."""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-Internal-Key", auto_error=False)


def verify_internal_key(api_key: str | None = Security(api_key_header)) -> str:
    """X-Internal-Key 헤더를 검증한다.

    Args:
        api_key: 요청 헤더에서 추출한 API 키.

    Returns:
        검증된 API 키 문자열.

    Raises:
        HTTPException: 키가 없거나 일치하지 않을 때 401 반환.
    """
    if not api_key or api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid internal key")
    return api_key
