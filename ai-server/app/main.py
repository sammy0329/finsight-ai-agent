import chromadb
from fastapi import FastAPI

from app.api.router import router as ai_router
from app.core.config import settings

app = FastAPI(title="FinSight AI Server", version="0.1.0")

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
