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
from datetime import datetime, timedelta, timezone

from app.pipeline.report_generator import REPORT_CONFIG, ReportType, run_report_pipeline

KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)

_VALID_TYPES = list(REPORT_CONFIG.keys())


def is_kst_weekday() -> bool:
    """KST 기준 평일(월~금) 여부를 반환한다."""
    return datetime.now(KST).weekday() < 5  # 0=월, 4=금, 5=토, 6=일


def infer_report_type_from_kst_hour() -> ReportType | None:
    """현재 KST 시각으로 리포트 타입을 추론한다.

    스케줄:
        KOR_PREMARKET  KST 08:00
        KOR_CLOSE      KST 16:45
        US_PREMARKET   KST 22:30 (서머타임) / KST 23:30 (서머타임 해제)
        US_CLOSE       KST 07:45

    Returns:
        추론된 ReportType 또는 None.
    """
    hour = datetime.now(KST).hour
    mapping: dict[int, ReportType] = {
        8: "KOR_PREMARKET",
        16: "KOR_CLOSE",
        22: "US_PREMARKET",  # 서머타임 (3~11월)
        23: "US_PREMARKET",  # 서머타임 해제 (11~3월)
        7: "US_CLOSE",
    }
    return mapping.get(hour)


def _get_report_type() -> ReportType:
    """환경 변수 또는 UTC 시각으로 리포트 타입을 결정한다."""
    env_type = os.environ.get("REPORT_TYPE", "").strip().upper()
    if env_type in _VALID_TYPES:
        return env_type  # type: ignore[return-value]

    inferred = infer_report_type_from_kst_hour()
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

    date = args.date or datetime.now(KST).strftime("%Y-%m-%d")

    try:
        report_type = _get_report_type()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # KST 주말에는 리포트를 생성하지 않음 (수동 실행 제외)
    # 단, US_CLOSE는 KST 토요일 허용 (UTC 금요일 미국 장 마감 데이터)
    if os.environ.get("REPORT_TYPE", "").strip() == "" and not is_kst_weekday():
        kst_now = datetime.now(KST)
        kst_weekday = kst_now.weekday()  # 5=토, 6=일
        if not (report_type == "US_CLOSE" and kst_weekday == 5):
            logger.info(
                "KST 주말(%s)이므로 리포트 생성을 건너뜁니다.",
                kst_now.strftime("%Y-%m-%d %a"),
            )
            sys.exit(0)

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
