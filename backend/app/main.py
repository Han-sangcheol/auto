"""
CleonAI Trading Platform Backend API

FastAPI 애플리케이션 메인 엔트리포인트
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db.session import engine, Base

# API 라우터
from .api.v1 import account, trading, market, logs, engine
from .api import websocket


# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "CleonAI Trading Platform API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# API 라우터 등록
app.include_router(
    account.router,
    prefix=f"{settings.API_V1_STR}/account",
    tags=["account"]
)
app.include_router(
    trading.router,
    prefix=f"{settings.API_V1_STR}/trading",
    tags=["trading"]
)
app.include_router(
    market.router,
    prefix=f"{settings.API_V1_STR}/market",
    tags=["market"]
)
app.include_router(
    logs.router,
    prefix=f"{settings.API_V1_STR}/logs",
    tags=["logs"]
)
app.include_router(
    engine.router,
    prefix=f"{settings.API_V1_STR}/engine",
    tags=["engine"]
)

# WebSocket 라우터 등록
app.include_router(
    websocket.router,
    tags=["websocket"]
)

# TODO: strategy 라우터 추가


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

