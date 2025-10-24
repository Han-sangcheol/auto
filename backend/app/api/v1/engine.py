"""
Trading Engine 제어 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
import signal
import psutil

router = APIRouter()

# 엔진 프로세스 저장
engine_process: Optional[subprocess.Popen] = None


class EngineStatus(BaseModel):
    """엔진 상태"""
    is_running: bool
    pid: Optional[int] = None
    status: str


class EngineConfig(BaseModel):
    """엔진 설정"""
    use_simulation: bool = True
    auto_trading: bool = False
    strategies: list = []


@router.get("/status", response_model=EngineStatus)
async def get_engine_status():
    """
    Trading Engine 상태 조회
    """
    global engine_process
    
    if engine_process is None:
        return EngineStatus(
            is_running=False,
            status="stopped"
        )
    
    # 프로세스가 실행 중인지 확인
    try:
        # poll()이 None이면 프로세스가 아직 실행 중
        if engine_process.poll() is None:
            return EngineStatus(
                is_running=True,
                pid=engine_process.pid,
                status="running"
            )
        else:
            engine_process = None
            return EngineStatus(
                is_running=False,
                status="stopped"
            )
    except Exception as e:
        return EngineStatus(
            is_running=False,
            status=f"error: {str(e)}"
        )


@router.post("/start")
async def start_engine(config: Optional[EngineConfig] = None):
    """
    Trading Engine 시작
    
    Parameters:
    - config: 엔진 설정 (선택)
    """
    global engine_process
    
    # 이미 실행 중인지 확인
    if engine_process is not None and engine_process.poll() is None:
        raise HTTPException(
            status_code=400,
            detail="Trading Engine is already running"
        )
    
    try:
        # Trading Engine 경로
        engine_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "..", "trading-engine"
        )
        engine_path = os.path.abspath(engine_path)
        
        # main.py 경로
        main_py = os.path.join(engine_path, "engine", "main.py")
        
        if not os.path.exists(main_py):
            raise HTTPException(
                status_code=500,
                detail=f"Trading Engine main.py not found: {main_py}"
            )
        
        # Python 실행 파일 (32-bit)
        # TODO: 32-bit Python 경로 설정
        python_exe = "python"  # 또는 python3, python32
        
        # 프로세스 시작
        engine_process = subprocess.Popen(
            [python_exe, main_py],
            cwd=engine_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return {
            "message": "Trading Engine started successfully",
            "pid": engine_process.pid,
            "status": "running"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start Trading Engine: {str(e)}"
        )


@router.post("/stop")
async def stop_engine():
    """
    Trading Engine 중지
    """
    global engine_process
    
    if engine_process is None or engine_process.poll() is not None:
        raise HTTPException(
            status_code=400,
            detail="Trading Engine is not running"
        )
    
    try:
        # 프로세스 종료
        pid = engine_process.pid
        
        # 먼저 SIGTERM으로 정상 종료 시도
        engine_process.terminate()
        
        # 5초 대기
        try:
            engine_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 강제 종료
            engine_process.kill()
            engine_process.wait()
        
        engine_process = None
        
        return {
            "message": "Trading Engine stopped successfully",
            "pid": pid,
            "status": "stopped"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop Trading Engine: {str(e)}"
        )


@router.post("/restart")
async def restart_engine(config: Optional[EngineConfig] = None):
    """
    Trading Engine 재시작
    """
    # 중지
    try:
        await stop_engine()
    except HTTPException:
        pass  # 이미 중지된 경우 무시
    
    # 시작
    return await start_engine(config)


@router.get("/logs")
async def get_engine_logs():
    """
    Trading Engine 로그 조회
    
    Returns:
    - 최근 로그 (stdout, stderr)
    """
    global engine_process
    
    if engine_process is None:
        return {
            "stdout": "",
            "stderr": "",
            "status": "not running"
        }
    
    try:
        # 비블로킹 읽기
        import select
        
        stdout_data = ""
        stderr_data = ""
        
        # stdout이 있으면 읽기
        if engine_process.stdout:
            # 사용 가능한 데이터가 있는지 확인 (Unix/Linux)
            # Windows에서는 다르게 처리해야 함
            try:
                stdout_data = engine_process.stdout.read()
            except:
                pass
        
        # stderr이 있으면 읽기
        if engine_process.stderr:
            try:
                stderr_data = engine_process.stderr.read()
            except:
                pass
        
        return {
            "stdout": stdout_data,
            "stderr": stderr_data,
            "pid": engine_process.pid,
            "status": "running" if engine_process.poll() is None else "stopped"
        }
    
    except Exception as e:
        return {
            "stdout": "",
            "stderr": "",
            "error": str(e)
        }

