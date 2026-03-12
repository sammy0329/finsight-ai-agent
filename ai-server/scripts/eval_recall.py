"""T-702: Retrieval Recall@5 평가 스크립트.

ChromaDB retriever가 각 질문에 대해 관련 문서를 top-K 내에 포함하는지 측정한다.

Recall@K 정의:
    각 쿼리에 대해 top-K 검색 결과 중 relevant_keywords 중 하나 이상을 포함하는
    문서가 존재하면 hit=1, 없으면 hit=0 으로 처리.
    Recall@K = sum(hits) / len(queries)

실행 방법:
    cd ai-server
    export $(cat ../.env | grep -v '^#' | xargs)
    poetry run python scripts/eval_recall.py [--top-k 5] [--output results/recall.json]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EVAL_QUESTIONS_PATH = Path(__file__).parents[2] / "docs" / "eval" / "eval_questions.json"
DEFAULT_OUTPUT = Path(__file__).parent / "results" / "recall.json"


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_recall(
    questions: list[dict],
    chroma_host: str,
    chroma_port: int,
    top_k: int = 5,
) -> dict:
    """각 질문에 대해 Recall@K를 계산한다.

    Args:
        questions: eval_questions.json 항목 리스트.
        chroma_host: ChromaDB 호스트.
        chroma_port: ChromaDB 포트.
        top_k: 검색 결과 수.

    Returns:
        results, recall_at_k, total, hits 포함 dict.
    """
    from app.agent.retriever import get_retriever

    results = []
    hits = 0

    for q in questions:
        query = q["query"]
        keywords = [kw.lower() for kw in q.get("relevant_keywords", [])]
        # 뉴스형·복합형만 retriever 평가 대상 (ChromaDB 사용 질문)
        if "search_news_tool" not in q.get("expected_tools", []):
            logger.info("SKIP %s (retriever 미사용 질문)", q["id"])
            continue

        # market 추론: 티커로 KOR/US 결정
        ticker = q.get("ticker", "")
        market = "US" if ticker.isalpha() and len(ticker) <= 5 else "KOR"

        try:
            retriever = get_retriever(
                chroma_host=chroma_host,
                chroma_port=chroma_port,
                market=market,
            )
            retriever.k = top_k  # type: ignore[attr-defined]
            docs = retriever.invoke(query)
        except Exception as e:
            logger.warning("retriever 오류 qid=%s: %s", q["id"], e)
            results.append({"id": q["id"], "hit": False, "error": str(e)})
            continue

        # hit 판정: top-K 문서 중 어느 하나가 keyword를 포함하면 hit
        combined_text = " ".join(doc.page_content.lower() for doc in docs)
        hit = any(kw in combined_text for kw in keywords)
        hits += int(hit)

        results.append(
            {
                "id": q["id"],
                "segment": q["segment"],
                "type": q["type"],
                "query": query,
                "hit": hit,
                "top_k_count": len(docs),
                "matched_keywords": [kw for kw in keywords if kw in combined_text],
            }
        )
        logger.info("[%s] %s → hit=%s", q["id"], query[:40], hit)

    evaluated = [r for r in results if "error" not in r or r.get("hit") is not None]
    recall = hits / len(evaluated) if evaluated else 0.0

    return {
        "metric": f"Recall@{top_k}",
        "recall": round(recall, 4),
        "hits": hits,
        "total_evaluated": len(evaluated),
        "target": 0.8,
        "pass": recall >= 0.8,
        "evaluated_at": datetime.now().isoformat(),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recall@K 평가")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    questions = load_questions(EVAL_QUESTIONS_PATH)
    logger.info("질문 로드: %d건", len(questions))

    chroma_host = os.environ.get("CHROMA_HOST", "localhost")
    chroma_port = int(os.environ.get("CHROMA_PORT", "8001"))

    summary = evaluate_recall(questions, chroma_host, chroma_port, top_k=args.top_k)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info("=== Recall@%d 결과 ===", args.top_k)
    logger.info(
        "Recall@%d : %.4f  (hit=%d / %d)",
        args.top_k,
        summary["recall"],
        summary["hits"],
        summary["total_evaluated"],
    )
    logger.info("목표 달성 : %s (목표 ≥ 0.80)", "✅" if summary["pass"] else "❌")
    logger.info("결과 저장 : %s", args.output)

    sys.exit(0 if summary["pass"] else 1)


if __name__ == "__main__":
    main()
