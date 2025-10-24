"""
로그 API 엔드포인트
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ...db.session import get_db
from ...db import models

router = APIRouter()


@router.get("/")
async def get_logs(
    limit: int = Query(1000, ge=1, le=10000),
    level: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    로그 조회
    
    Parameters:
    - limit: 조회할 로그 개수 (기본: 1000, 최대: 10000)
    - level: 로그 레벨 필터 (DEBUG, INFO, WARNING, ERROR)
    - module: 모듈 필터
    - start_time: 시작 시간 (이 시간 이후의 로그만 조회)
    """
    query = db.query(models.SystemLog)
    
    # 필터 적용
    if level:
        query = query.filter(models.SystemLog.level == level)
    
    if module:
        query = query.filter(models.SystemLog.module == module)
    
    if start_time:
        query = query.filter(models.SystemLog.timestamp >= start_time)
    
    # 최신 로그부터 정렬
    query = query.order_by(models.SystemLog.timestamp.desc())
    
    # 제한
    logs = query.limit(limit).all()
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "module": log.module,
            "message": log.message
        }
        for log in logs
    ]


@router.post("/")
async def create_log(
    level: str,
    module: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    로그 생성
    
    Parameters:
    - level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
    - module: 모듈 이름
    - message: 로그 메시지
    """
    log = models.SystemLog(
        level=level,
        module=module,
        message=message,
        timestamp=datetime.utcnow()
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return {
        "id": log.id,
        "timestamp": log.timestamp.isoformat(),
        "level": log.level,
        "module": log.module,
        "message": log.message
    }


@router.delete("/")
async def clear_logs(
    older_than_days: int = Query(30, ge=1),
    db: Session = Depends(get_db)
):
    """
    오래된 로그 삭제
    
    Parameters:
    - older_than_days: 이 일수보다 오래된 로그 삭제 (기본: 30일)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
    
    deleted_count = db.query(models.SystemLog).filter(
        models.SystemLog.timestamp < cutoff_date
    ).delete()
    
    db.commit()
    
    return {
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.get("/stats")
async def get_log_stats(
    db: Session = Depends(get_db)
):
    """
    로그 통계 조회
    
    Returns:
    - 총 로그 수
    - 레벨별 로그 수
    - 최근 24시간 로그 수
    """
    from sqlalchemy import func
    
    # 총 로그 수
    total_count = db.query(func.count(models.SystemLog.id)).scalar()
    
    # 레벨별 로그 수
    level_counts = db.query(
        models.SystemLog.level,
        func.count(models.SystemLog.id)
    ).group_by(models.SystemLog.level).all()
    
    # 최근 24시간 로그 수
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_count = db.query(func.count(models.SystemLog.id)).filter(
        models.SystemLog.timestamp >= last_24h
    ).scalar()
    
    return {
        "total_count": total_count,
        "level_counts": {level: count for level, count in level_counts},
        "recent_24h_count": recent_count
    }

