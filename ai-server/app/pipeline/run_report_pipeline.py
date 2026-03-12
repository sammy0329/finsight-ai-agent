"""T-610~T-613: 리포트 파이프라인 CLI 실행 스크립트.

환경 변수:
    SUPABASE_URL              — Supabase 프로젝트 URL
    SUPABASE_SERVICE_ROLE_KEY — service role key
    OPENAI_API_KEY            — OpenAI API 키
    CHROMA_HOST               — ChromaDB 호스트 (기본: localhost)
    CHROMA_PORT               — ChromaDB 포트 (기본: 8001)
    REPORT_TYPE               — 리포트 타입 (KOR_PREMARKET | KOR_CLOSE | US_PREMARKET | US_CLOSE)

CLI 실행 예시:
    REPORT_TYPE=KOR_CLOSE python -m app.pipeline.run_report_pipeline
    REPORT_TYPE=US_CLOSE  python -m app.pipeline.run_report_pipeline --date 2026-03-13
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone

from app.pipeline.report_generator import REPORT_CONFIG, ReportType, run_report_pipeline

logger = logging.getLogger(__name__)

_VALID_TYPES = list(REPORT_CONFIG.keys())


def infer_report_type_from_utc_hour() -> ReportType | None:
    """현재 UTC 시각으로 리포트 타입을 추론한다.

    스케줄:
        KOR_PREMARKET  UTC 23:00 (KST 08:00)
        KOR_CLOSE      UTC 07:30 (KST 16:30)
        US_PREMARKET   UTC 13:30 (KST 22:30)
        US_CLOSE       UTC 22:30 (KST 07:30)

    Returns:
        추론된 ReportType 또는 None.
    """
    hour = datetime.now(timezone.utc).hour
    mapping: dict[int, ReportType] = {
        23: "KOR_PREMARKET",
        7: "KOR_CLOSE",
        13: "US_PREMARKET",
        22: "US_CLOSE",
    }
    return mapping.get(hour)


def _get_report_type() -> ReportType:
    """환경 변수 또는 UTC 시각으로 리포트 타입을 결정한다."""
    env_type = os.environ.get("REPORT_TYPE", "").strip().upper()
    if env_type in _VALID_TYPES:
        return env_type  # type: ignore[return-value]

    inferred = infer_report_type_from_utc_hour()
    if inferred:
        logger.info("REPORT_TYPE 미설정 — UTC 시각 기반 추론: %s", inferred)
        return inferred

    raise ValueError(
        f"REPORT_TYPE을 결정할 수 없습니다. 환경 변수로 명시적으로 설정하세요: {_VALID_TYPES}"
    )


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="FinSight 리포트 파이프라인")
    parser.add_argument("--date", default="", help="기준일 YYYY-MM-DD (미입력 시 오늘)")
    args = parser.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        report_type = _get_report_type()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    config = {
        "supabase_url": os.environ["SUPABASE_URL"],
        "supabase_key": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "openai_api_key": os.environ["OPENAI_API_KEY"],
        "chroma_host": os.environ.get("CHROMA_HOST", "localhost"),
        "chroma_port": int(os.environ.get("CHROMA_PORT", "8001")),
        "date": date,
    }

    logger.info("리포트 파이프라인 시작: type=%s date=%s", report_type, date)
    result = run_report_pipeline(report_type, config)
    logger.info("리포트 파이프라인 완료: %s", result)

    sys.exit(0 if result.get("success") else 1)
