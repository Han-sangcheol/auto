"""
매매 관련 API 엔드포인트

주문 실행, 취소, 조회 API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.repositories import order_repo, trade_repo, account_repo, position_repo
from ...schemas.order import OrderCreate, OrderResponse, OrderCancelRequest
from ...schemas.trade import TradeResponse, TradeSummary

router = APIRouter()


@router.post("/order", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db)
):
    """주문 실행"""
    # 계좌 존재 확인
    account = account_repo.get(db, order_in.account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # 매도 주문인 경우 포지션 확인
    if order_in.order_type == 'sell':
        position = position_repo.get_by_stock(
            db, order_in.account_id, order_in.stock_code
        )
        if not position or position.quantity < order_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient position"
            )
    
    # 매수 주문인 경우 잔고 확인
    if order_in.order_type == 'buy':
        required_amount = order_in.quantity * (order_in.price or 0)
        if order_in.price_type == 'market':
            # 시장가의 경우 대략적인 금액 체크 (여유분 10%)
            required_amount = order_in.quantity * 100000  # 임시
        
        if account.current_balance < required_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
    
    # 주문 생성
    order = order_repo.create(db, order_in.model_dump())
    
    # TODO: Trading Engine에 주문 전송 (Redis Queue)
    
    return order


@router.delete("/order/{order_id}", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """주문 취소"""
    order = order_repo.get(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status: {order.status}"
        )
    
    # TODO: Trading Engine에 취소 요청
    
    cancelled_order = order_repo.cancel_order(db, order_id)
    return cancelled_order


@router.get("/orders/{account_id}", response_model=List[OrderResponse])
def get_orders(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """주문 목록 조회"""
    orders = order_repo.get_by_account(db, account_id, skip, limit)
    return orders


@router.get("/orders/{account_id}/pending", response_model=List[OrderResponse])
def get_pending_orders(
    account_id: int,
    db: Session = Depends(get_db)
):
    """대기 중인 주문 목록"""
    orders = order_repo.get_pending_orders(db, account_id)
    return orders


@router.get("/trades/{account_id}", response_model=List[TradeResponse])
def get_trades(
    account_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """거래 내역 조회"""
    trades = trade_repo.get_by_account(db, account_id, skip, limit)
    return trades


@router.get("/trades/{account_id}/summary", response_model=TradeSummary)
def get_trade_summary(
    account_id: int,
    db: Session = Depends(get_db)
):
    """거래 요약 통계"""
    summary = trade_repo.get_trade_summary(db, account_id)
    return summary

