from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db  # Import the database session dependency
from app.models import User
from app import schemas, security

router = APIRouter()

# Get all users from the database
@router.get("/")
def get_users(db: Session = Depends(get_db)):  # Use dependency injection for session
    users = db.query(User).all()
    return users

# Add a new user to the database
@router.post("/add_user")
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_pw = security.hash_password(user.password).decode('utf-8')
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "User added!"}
