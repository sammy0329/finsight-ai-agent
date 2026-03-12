# FinSight Agent — 품질 평가 결과

> 평가 환경: EC2 배포 후 실서버 기준 측정 (Phase 4 완료 후 실행)
> 스크립트: `ai-server/scripts/eval_recall.py`, `ai-server/scripts/eval_tool_selection.py`
> 질문 세트: `docs/eval/eval_questions.json` (30건, 세그먼트별 10건)

---

## 1. Retrieval 품질 — Recall@5

| 항목 | 값 | 목표 | 달성 |
|---|---|---|---|
| Recall@5 (전체) | — | ≥ 80% | — |
| Recall@5 (KOR) | — | ≥ 80% | — |
| Recall@5 (US) | — | ≥ 80% | — |

> **측정 방법**: 뉴스형 질문 17건에 대해 ChromaDB retriever top-5 결과에
> 사전 정의된 관련 키워드가 1개 이상 포함되면 hit=1 처리.

### 세그먼트별 Recall@5

| 세그먼트 | 질문 수 | 뉴스형 | Recall@5 |
|---|---|---|---|
| A (안전추구형) | 10 | 4 | — |
| B (위험감수형) | 10 | 4 | — |
| C (가치투자형) | 10 | 4 | — |

### 최적화 실험 (T-707~T-709)

| 설정 | Recall@3 | Recall@5 | Recall@10 |
|---|---|---|---|
| chunk=300, top_k=5 | — | — | — |
| chunk=500, top_k=5 | — | — | — |
| chunk=700, top_k=5 | — | — | — |
| chunk=500, top_k=3 | — | — | — |
| chunk=500, top_k=10 | — | — | — |

---

## 2. 도구 선택 정확도 (T-703)

| 항목 | 값 | 목표 | 달성 |
|---|---|---|---|
| 전체 정확도 | — | ≥ 85% | — |
| A형 정확도 | — | ≥ 85% | — |
| B형 정확도 | — | ≥ 85% | — |
| C형 정확도 | — | ≥ 85% | — |

### 도구 타입별 정확도

| 질문 타입 | 건수 | 정확도 |
|---|---|---|
| 뉴스형 (search_news_tool) | 9 | — |
| 공시형 (get_dart_tool) | 3 | — |
| 가격형 (get_price_tool / price_anomaly_tool) | 8 | — |
| 재무형 (get_financials_tool) | 5 | — |
| 복합형 (multi-tool) | 5 | — |

---

## 3. 환각(Hallucination) 비율 (T-705)

| 항목 | 값 | 목표 | 달성 |
|---|---|---|---|
| 환각 비율 (전체) | — | ≤ 10% | — |
| A형 환각 비율 | — | ≤ 10% | — |
| B형 환각 비율 | — | ≤ 10% | — |
| C형 환각 비율 | — | ≤ 10% | — |

> **판정 기준**: 답변이 30자 미만이거나, 질문 티커 미언급 + 부정 응답 문구만 포함된 경우.

---

## 4. 세그먼트 적합성 정성 평가 (T-704)

동일 질문 `"삼성전자 지금 매수해도 돼?"` 를 3개 세그먼트에 각각 질의한 결과:

### A형 (안전추구형) 응답 요약
> — (평가 후 기재)

**체크리스트:**
- [ ] 리스크·손실 가능성 언급
- [ ] 배당·안정성 관점 제시
- [ ] 투기적 표현 없음

### B형 (위험감수형) 응답 요약
> — (평가 후 기재)

**체크리스트:**
- [ ] 모멘텀·성장 관점 강조
- [ ] 상승 기회 언급
- [ ] 과도한 리스크 경고 없음

### C형 (가치투자형) 응답 요약
> — (평가 후 기재)

**체크리스트:**
- [ ] PER/PBR/ROE 언급
- [ ] 내재가치·저평가 여부 분석
- [ ] 장기 관점 제시

---

## 5. 응답 시간 측정 (T-710)

| 측정 항목 | 값 | 목표 |
|---|---|---|
| P50 (중간값) | — | < 3초 |
| P95 (95th percentile) | — | < 5초 |
| P99 | — | < 8초 |
| 최대 응답 시간 | — | — |

> **측정 방법**: 30개 질문 각각에 대해 첫 토큰 도달까지의 시간 (TTFT) 측정.

---

## 6. 평가 실행 방법

```bash
# 환경 설정
cd ai-server
export $(cat ../.env | grep -v '^#' | xargs)

# Recall@5 측정 (ChromaDB 접근 필요)
poetry run python scripts/eval_recall.py --top-k 5 --output scripts/results/recall.json

# 도구 선택 정확도 + 환각 비율 (OpenAI API 호출 발생)
poetry run python scripts/eval_tool_selection.py --output scripts/results/tool_selection.json

# 세그먼트별 평가
poetry run python scripts/eval_tool_selection.py --segment A
poetry run python scripts/eval_tool_selection.py --segment B
poetry run python scripts/eval_tool_selection.py --segment C
```

---

## 7. 최종 평가 요약

| 지표 | 값 | 목표 | 달성 |
|---|---|---|---|
| Recall@5 | — | ≥ 80% | — |
| 도구 선택 정확도 | — | ≥ 85% | — |
| 환각 비율 | — | ≤ 10% | — |
| P95 응답 시간 | — | < 5초 | — |

> **마지막 업데이트**: Phase 4 (EC2 배포) 완료 후 측정 예정
