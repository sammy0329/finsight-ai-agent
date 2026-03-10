"""Epic 2 테스트 공통 설정."""

import os

# Settings 로드 전에 환경변수 기본값 설정 (테스트 환경)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
