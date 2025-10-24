"""
계좌 관련 API 엔드포인트

계좌 조회, 잔고 확인, 포지션 관리 API
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...db.repositories import account_repo, position_repo
from ...schemas.account import AccountResponse, AccountBalanceResponse
from ...schemas.position import PositionResponse

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    user_id: int = 1,  # TODO: JWT에서 가져오기
    db: Session = Depends(get_db)
):
    """사용자의 계좌 목록 조회"""
    accounts = account_repo.get_by_user(db, user_id)
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """특정 계좌 조회"""
    account = account_repo.get(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
def get_account_balance(
    account_id: int,
    db: Session = Depends(get_db)
):
    """계좌 잔고 및 요약 정보"""
    summary = account_repo.get_account_summary(db, account_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return summary


@router.get("/{account_id}/positions", response_model=List[PositionResponse])
def get_account_positions(
    account_id: int,
    db: Session = Depends(get_db)
):
    """계좌의 포지션 목록"""
    # 계좌 존재 확인
    account = account_repo.get(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    positions = position_repo.get_by_account(db, account_id)
    return positions


@router.get("/{account_id}/positions/{stock_code}", response_model=PositionResponse)
def get_position_by_stock(
    account_id: int,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """특정 종목 포지션 조회"""
    position = position_repo.get_by_stock(db, account_id, stock_code)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    return position

