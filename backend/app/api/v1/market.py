"""
시세 관련 API 엔드포인트

실시간 시세, 차트 데이터, 급등주 정보 API
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.models import MarketData, SurgeDetection

router = APIRouter()


@router.get("/stocks/{stock_code}")
def get_stock_info(
    stock_code: str,
    db: Session = Depends(get_db)
):
    """종목 정보 조회"""
    # 최근 시세 데이터 조회
    latest_data = db.query(MarketData).filter(
        MarketData.stock_code == stock_code
    ).order_by(MarketData.timestamp.desc()).first()
    
    if not latest_data:
        raise HTTPException(
            status_code=404,
            detail=f"Stock {stock_code} not found"
        )
    
    return {
        'stock_code': stock_code,
        'timestamp': latest_data.timestamp,
        'open_price': latest_data.open_price,
        'high_price': latest_data.high_price,
        'low_price': latest_data.low_price,
        'close_price': latest_data.close_price,
        'volume': latest_data.volume,
        'trade_value': latest_data.trade_value,
        'change_rate': latest_data.change_rate,
    }


@router.get("/stocks/{stock_code}/chart")
def get_chart_data(
    stock_code: str,
    days: int = Query(default=7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """차트 데이터 조회 (OHLCV)"""
    since = datetime.utcnow() - timedelta(days=days)
    
    data = db.query(MarketData).filter(
        MarketData.stock_code == stock_code,
        MarketData.timestamp >= since
    ).order_by(MarketData.timestamp).all()
    
    if not data:
        return {
            'stock_code': stock_code,
            'period_days': days,
            'data_count': 0,
            'data': []
        }
    
    return {
        'stock_code': stock_code,
        'period_days': days,
        'data_count': len(data),
        'data': [
            {
                'timestamp': d.timestamp,
                'open': d.open_price,
                'high': d.high_price,
                'low': d.low_price,
                'close': d.close_price,
                'volume': d.volume,
            } for d in data
        ]
    }


@router.get("/surge")
def get_surge_stocks(
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """급등주 목록 조회"""
    query = db.query(SurgeDetection)
    
    if status:
        query = query.filter(SurgeDetection.status == status)
    
    # 최근 24시간 이내
    since = datetime.utcnow() - timedelta(hours=24)
    surge_stocks = query.filter(
        SurgeDetection.detection_time >= since
    ).order_by(
        SurgeDetection.detection_time.desc()
    ).limit(limit).all()
    
    return {
        'count': len(surge_stocks),
        'stocks': [
            {
                'id': s.id,
                'stock_code': s.stock_code,
                'stock_name': s.stock_name,
                'detection_time': s.detection_time,
                'price': s.price,
                'change_rate': float(s.change_rate),
                'volume': s.volume,
                'volume_ratio': float(s.volume_ratio),
                'status': s.status,
            } for s in surge_stocks
        ]
    }


@router.post("/surge/{surge_id}/approve")
def approve_surge_stock(
    surge_id: int,
    db: Session = Depends(get_db)
):
    """급등주 승인"""
    surge = db.query(SurgeDetection).filter(
        SurgeDetection.id == surge_id
    ).first()
    
    if not surge:
        raise HTTPException(status_code=404, detail="Surge detection not found")
    
    surge.status = 'approved'
    surge.approved_at = datetime.utcnow()
    db.commit()
    
    # TODO: Trading Engine에 매수 신호 전송
    
    return {'message': 'Surge stock approved', 'surge_id': surge_id}


@router.post("/surge/{surge_id}/reject")
def reject_surge_stock(
    surge_id: int,
    db: Session = Depends(get_db)
):
    """급등주 거부"""
    surge = db.query(SurgeDetection).filter(
        SurgeDetection.id == surge_id
    ).first()
    
    if not surge:
        raise HTTPException(status_code=404, detail="Surge detection not found")
    
    surge.status = 'rejected'
    db.commit()
    
    return {'message': 'Surge stock rejected', 'surge_id': surge_id}

