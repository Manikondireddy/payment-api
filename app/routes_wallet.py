import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import get_db
from app.schemas import WalletOperation, WalletResponse
from app import services

router = APIRouter(prefix="/wallet", tags=["wallet"])
logger = logging.getLogger("payment-api.wallet")


@router.post("/{customer_id}/credit", response_model=WalletResponse)
def credit_wallet(customer_id: str, operation: WalletOperation, db: Session = Depends(get_db)):
    """Credit amount to customer wallet."""
    try:
        wallet = services.credit_wallet(db, customer_id, operation.amount)
        return WalletResponse(customer_id=wallet.customer_id, balance=float(wallet.balance))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid customer_id")
    except Exception:
        logger.exception("Wallet credit failed for customer_id=%s", customer_id)
        raise HTTPException(status_code=500, detail="Wallet credit failed")


@router.post("/{customer_id}/debit", response_model=WalletResponse)
def debit_wallet(customer_id: str, operation: WalletOperation, db: Session = Depends(get_db)):
    """Debit amount from customer wallet."""
    try:
        wallet = services.debit_wallet(db, customer_id, operation.amount)
        return WalletResponse(customer_id=wallet.customer_id, balance=float(wallet.balance))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid customer_id")
    except Exception:
        logger.exception("Wallet debit failed for customer_id=%s", customer_id)
        raise HTTPException(status_code=500, detail="Wallet debit failed")


@router.get("/{customer_id}", response_model=WalletResponse)
def get_wallet(customer_id: str, db: Session = Depends(get_db)):
    """Get wallet balance for a customer."""
    try:
        wallet = services.get_wallet(db, customer_id)
        return WalletResponse(customer_id=wallet.customer_id, balance=float(wallet.balance))
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid customer_id")
    except Exception:
        logger.exception("Wallet lookup failed for customer_id=%s", customer_id)
        raise HTTPException(status_code=500, detail="Wallet lookup failed")
