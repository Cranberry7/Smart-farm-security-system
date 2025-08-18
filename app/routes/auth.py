from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .. import models, schemas, security
from ..database import get_db

router = APIRouter()

# User Registration Endpoint
@router.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the user's password and save user to the database
    hashed_password = security.hash_password(user.password).decode('utf-8')
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}

# User Login Endpoint
@router.post("/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    # Fetch user from the database
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not security.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token and return it
    token = security.create_token({"user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}
