# GitHub Actions Secrets 등록 가이드

GitHub 레포지토리 → Settings → Secrets and variables → Actions → New repository secret

## 필수 Secrets

| Secret 키 | 설명 | 발급처 |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API 인증 키 | https://platform.openai.com/api-keys |
| `DART_API_KEY` | 금융감독원 OpenDart API 키 | https://opendart.fss.or.kr |
| `NAVER_CLIENT_ID` | Naver Search API Client ID | https://developers.naver.com |
| `NAVER_CLIENT_SECRET` | Naver Search API Client Secret | https://developers.naver.com |
| `NEWS_API_KEY` | NewsAPI 인증 키 | https://newsapi.org |
| `INTERNAL_API_KEY` | Spring Boot ↔ FastAPI 내부 인증 키 | 직접 생성 (32자 이상 랜덤 문자열) |

## EC2 접속 Secrets (배포 후 등록)

| Secret 키 | 설명 | 생성 방법 |
|---|---|---|
| `EC2_HOST` | EC2 탄력적 IP 주소 | AWS Console에서 확인 |
| `EC2_SSH_KEY` | EC2 접속용 PEM 키 (Base64 인코딩) | `base64 -i finsight-key.pem` |

## 알림 Secrets (선택)

| Secret 키 | 설명 | 발급처 |
|---|---|---|
| `SLACK_WEBHOOK_URL` | 파이프라인 알림용 Slack Webhook | Slack App 설정 → Incoming Webhooks |

## EC2_SSH_KEY 생성 방법

```bash
# PEM 키를 Base64로 인코딩하여 복사
base64 -i finsight-key.pem | pbcopy   # macOS
base64 -w 0 finsight-key.pem | xclip  # Linux
```
