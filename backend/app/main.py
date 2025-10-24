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

# Redis Subscriber (이벤트 수신)
from .services.redis_subscriber import RedisEventSubscriber
redis_subscriber = None

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


# Startup/Shutdown 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    global redis_subscriber
    
    # Redis Subscriber 시작
    redis_subscriber = RedisEventSubscriber(
        redis_url=settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://localhost:6379"
    )
    
    if redis_subscriber.connect():
        from .api.websocket import broadcast_to_all
        
        # 각 채널별 핸들러 등록
        redis_subscriber.subscribe('trading:orders', 
            lambda data: asyncio.create_task(broadcast_to_all('orders', data)))
        redis_subscriber.subscribe('trading:positions', 
            lambda data: asyncio.create_task(broadcast_to_all('positions', data)))
        redis_subscriber.subscribe('market:data', 
            lambda data: asyncio.create_task(broadcast_to_all('market', data)))
        redis_subscriber.subscribe('trading:surge', 
            lambda data: asyncio.create_task(broadcast_to_all('surge', data)))
        
        # 백그라운드에서 수신 시작
        asyncio.create_task(redis_subscriber.start_listening())


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    global redis_subscriber
    
    if redis_subscriber:
        redis_subscriber.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

