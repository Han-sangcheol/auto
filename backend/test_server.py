"""
간단한 테스트 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CleonAI Trading Platform - Test Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "CleonAI Trading Platform API",
        "status": "running",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "development",
    }

@app.get("/api/v1/account")
async def get_accounts():
    """계좌 정보 조회 (테스트용)"""
    return [
        {
            "id": 1,
            "broker": "kiwoom",
            "account_no": "8113110311",        # 실제 계좌번호
            "account_name": "모의투자계좌",      # 계좌명
            "account_type": "simulation",       # simulation 또는 real
            "balance": 10000000,
            "initial_balance": 10000000,
            "is_active": True
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


