from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.auth.schemas import RegisterRequest, LoginRequest
from app.auth.hashing import get_password_hash, verify_password
from app.auth.jwt_handler import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# 🔹 REGISTER
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = get_password_hash(data.password)

    new_user = User(
        username=data.username,
        email=data.email or "",
        hashed_password=hashed_password    # ← fixed (was password=)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully"}


# 🔹 LOGIN
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.hashed_password):  # ← fixed
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# 🔹 GET CURRENT USER
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email or ""
    }


# 🔹 GET ALL USERS
@router.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).filter(User.id != current_user.id).all()
    return [
        {
            "id": str(u.id),
            "username": u.username,
            "email": u.email or ""
        }
        for u in users
    ]