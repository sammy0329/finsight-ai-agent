import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as ai_router
from app.core.config import settings

app = FastAPI(title="FinSight AI Server", version="0.1.0")

# T-410: CORS 설정 (Vercel 도메인 + 로컬 개발 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Internal-Key"],
)

# 라우터 등록
app.include_router(ai_router)


@app.get("/health")
async def health():
    """헬스체크 엔드포인트. ChromaDB 연결 상태를 포함한다."""
    chroma_status = "disconnected"
    try:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        client.heartbeat()
        chroma_status = "connected"
    except Exception:
        pass
    return {"status": "ok", "chroma": chroma_status}
