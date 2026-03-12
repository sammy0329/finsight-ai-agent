"""T-703/T-705: 도구 선택 정확도 + 환각 비율 평가 스크립트.

도구 선택 정확도 (T-703):
    각 질문에 대해 AgentExecutor가 호출한 첫 번째(주요) 도구가
    expected_tools의 첫 번째 항목과 일치하면 correct.
    Accuracy = correct / total  (목표 ≥ 85%)

환각 비율 (T-705):
    응답에 질문 ticker가 전혀 언급되지 않거나, "알 수 없습니다" 수준의 무관한 답변이면
    hallucination=True 로 마킹.
    Hallucination Rate = hallucinated / total  (목표 ≤ 10%)

실행 방법:
    cd ai-server
    export $(cat ../.env | grep -v '^#' | xargs)
    poetry run python scripts/eval_tool_selection.py [--output results/tool_selection.json]

주의: OpenAI API 호출이 발생합니다 (질문당 약 1회).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EVAL_QUESTIONS_PATH = Path(__file__).parents[2] / "docs" / "eval" / "eval_questions.json"
DEFAULT_OUTPUT = Path(__file__).parent / "results" / "tool_selection.json"

# 환각 판정용 부정 키워드 (이 문구만 포함된 경우 환각으로 의심)
_HALLUCINATION_PHRASES = [
    "알 수 없습니다",
    "정보가 없습니다",
    "데이터가 없습니다",
    "찾을 수 없습니다",
    "제공할 수 없습니다",
]


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ToolCallTracker:
    """LangChain 콜백 없이 도구 호출을 추적하기 위한 래퍼."""

    def __init__(self) -> None:
        self.called_tools: list[str] = []

    def reset(self) -> None:
        self.called_tools = []


def run_agent_with_tracking(
    executor,
    query: str,
    tracker: ToolCallTracker,
) -> str:
    """AgentExecutor를 동기 실행하고 호출된 도구 목록을 tracker에 기록한다."""
    from langchain_core.callbacks import BaseCallbackHandler

    class ToolTrackingCallback(BaseCallbackHandler):
        def on_tool_start(self, serialized, input_str, **kwargs):  # type: ignore
            tool_name = serialized.get("name", "")
            tracker.called_tools.append(tool_name)

    tracker.reset()
    result = executor.invoke(
        {"input": query},
        config={"callbacks": [ToolTrackingCallback()]},
    )
    return result.get("output", "")


def is_hallucination(answer: str, ticker: str) -> bool:
    """응답이 환각(무관하거나 근거 없는 답변)인지 판정한다.

    단순 휴리스틱:
    1. 답변이 너무 짧음 (< 30자)
    2. 부정 키워드만 포함하고 ticker 미언급
    """
    if len(answer.strip()) < 30:
        return True
    ticker_lower = ticker.lower()
    answer_lower = answer.lower()
    has_ticker = ticker_lower in answer_lower
    only_negative = any(phrase in answer for phrase in _HALLUCINATION_PHRASES)
    return only_negative and not has_ticker


def evaluate_tool_selection(
    questions: list[dict],
    openai_api_key: str,
    chroma_host: str,
    chroma_port: int,
    delay_sec: float = 1.0,
) -> dict:
    """전체 질문에 대해 도구 선택 정확도와 환각 비율을 계산한다."""
    from app.agent.executor import create_agent_executor

    results = []
    correct_tool = 0
    hallucinated = 0

    for q in questions:
        segment = q["segment"]
        query = q["query"]
        expected_first_tool = q["expected_tools"][0]
        ticker = q.get("ticker", "")

        try:
            executor = create_agent_executor(
                segment=segment,
                openai_api_key=openai_api_key,
                chroma_host=chroma_host,
                chroma_port=chroma_port,
            )
            tracker = ToolCallTracker()
            answer = run_agent_with_tracking(executor, query, tracker)
        except Exception as e:
            logger.warning("실행 오류 qid=%s: %s", q["id"], e)
            results.append({"id": q["id"], "error": str(e)})
            continue

        first_called = tracker.called_tools[0] if tracker.called_tools else "none"
        tool_correct = first_called == expected_first_tool
        hallucination = is_hallucination(answer, ticker)

        if tool_correct:
            correct_tool += 1
        if hallucination:
            hallucinated += 1

        results.append(
            {
                "id": q["id"],
                "segment": segment,
                "type": q["type"],
                "query": query,
                "expected_tool": expected_first_tool,
                "first_called_tool": first_called,
                "all_called_tools": tracker.called_tools,
                "tool_correct": tool_correct,
                "hallucination": hallucination,
                "answer_length": len(answer),
                "answer_preview": answer[:200],
            }
        )

        status = "✅" if tool_correct else "❌"
        hall_status = "🚨" if hallucination else ""
        logger.info(
            "[%s] %s | 기대:%s 실제:%s %s%s",
            q["id"],
            query[:35],
            expected_first_tool,
            first_called,
            status,
            hall_status,
        )

        time.sleep(delay_sec)

    evaluated = [r for r in results if "error" not in r]
    n = len(evaluated)
    accuracy = correct_tool / n if n else 0.0
    hallucination_rate = hallucinated / n if n else 0.0

    return {
        "tool_selection_accuracy": round(accuracy, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "correct_tool": correct_tool,
        "hallucinated": hallucinated,
        "total_evaluated": n,
        "accuracy_target": 0.85,
        "hallucination_target": 0.10,
        "accuracy_pass": accuracy >= 0.85,
        "hallucination_pass": hallucination_rate <= 0.10,
        "evaluated_at": datetime.now().isoformat(),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="도구 선택 정확도 + 환각 비율 평가")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--delay", type=float, default=1.0, help="API 호출 간격 (초)")
    parser.add_argument("--segment", choices=["A", "B", "C", "ALL"], default="ALL")
    args = parser.parse_args()

    questions = load_questions(EVAL_QUESTIONS_PATH)
    if args.segment != "ALL":
        questions = [q for q in questions if q["segment"] == args.segment]
    logger.info("평가 대상: %d건 (segment=%s)", len(questions), args.segment)

    openai_api_key = os.environ["OPENAI_API_KEY"]
    chroma_host = os.environ.get("CHROMA_HOST", "localhost")
    chroma_port = int(os.environ.get("CHROMA_PORT", "8001"))

    summary = evaluate_tool_selection(
        questions, openai_api_key, chroma_host, chroma_port, delay_sec=args.delay
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info("=== 평가 결과 ===")
    logger.info(
        "도구 선택 정확도 : %.1f%%  %s (목표 ≥ 85%%)",
        summary["tool_selection_accuracy"] * 100,
        "✅" if summary["accuracy_pass"] else "❌",
    )
    logger.info(
        "환각 비율       : %.1f%%  %s (목표 ≤ 10%%)",
        summary["hallucination_rate"] * 100,
        "✅" if summary["hallucination_pass"] else "❌",
    )
    logger.info("결과 저장 : %s", args.output)

    all_pass = summary["accuracy_pass"] and summary["hallucination_pass"]
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
