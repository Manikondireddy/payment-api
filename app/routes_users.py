import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.schemas import UserCreate, UserResponse, UserDetail
from app import services
from app.auth import get_current_user  
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("payment-api.users")  # Logger specific for users routes

@router.post("", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user (Sign Up). Public endpoint."""
    try:
        new_user = services.create_user(db, user)
        logger.info("User created successfully: user_id=%s", new_user.user_id)
        return new_user
    except ValueError as e:
        logger.warning("User creation failed: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as exc:
        logger.warning("User creation raised HTTPException: %s", exc.detail)
        raise

@router.get("/{user_id}", response_model=UserDetail)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user details by user ID. Protected endpoint."""
    try:
        if current_user.user_id != user_id:
            logger.warning("Unauthorized access attempt: current_user=%s, target_user=%s",
                           current_user.user_id, user_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's data"
            )
        
        user = services.get_user(db, user_id)
        if not user:
            logger.warning("User not found: user_id=%s", user_id)
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info("User fetched successfully: user_id=%s", user_id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching user: user_id=%s", user_id)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("", response_model=List[UserDetail])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users. Protected endpoint."""
    try:
        users = services.list_users(db, skip=skip, limit=limit)
        logger.info("Users listed successfully: count=%d, requested_by=%s", len(users), current_user.user_id)
        return users
    except Exception as e:
        logger.exception("Failed to list users")
        raise HTTPException(status_code=500, detail="Internal server error")