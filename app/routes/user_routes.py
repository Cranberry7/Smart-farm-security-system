from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db  # Import the database session dependency
from app.models import User
from app import schemas, security
from app.auth_dependency import get_current_user

router = APIRouter()

# Get current authenticated user
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.
    Requires a valid JWT token in the Authorization header.
    """
    return current_user

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
