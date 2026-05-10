from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserOut, Token
from auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_active_user,
)


router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    # Check username not already taken
    if db.query(User).filter(
        User.username == user_in.username
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Check email not already registered
    if db.query(User).filter(
        User.email == user_in.email
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create the user
    user = User(
        username        = user_in.username,
        email           = user_in.email,
        hashed_password = hash_password(user_in.password),
        full_name       = user_in.full_name,
        role            = "student",
        is_active       = True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)  # type: ignore[assignment]
    db.commit()

    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user.username)}
    )

    return Token(
        access_token = access_token,
        token_type   = "bearer",
        user         = UserOut.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserOut,
)
def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user