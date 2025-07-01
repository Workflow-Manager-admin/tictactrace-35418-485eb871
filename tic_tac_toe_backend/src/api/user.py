"""User router for user creation and (optional) login endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models, schemas

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PUBLIC_INTERFACE
@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, summary="Create New User", description="Register a new user with a unique username.")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create new user. Username must be unique."""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# (Optional demo "login" by username, for frontend to use, no passwords - not real auth)
# PUBLIC_INTERFACE
@router.post("/login", response_model=schemas.UserResponse, summary="Demo Login", description="Obtain user info if username exists (demo auth, not secure).")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Demo login by username (NOT secure, just returns user data)."""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
