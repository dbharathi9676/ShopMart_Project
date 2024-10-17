from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.user import User
from validator.user import UserValidator
from utilities.database import SessionLocal
from typing import List, Annotated

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", response_model=UserValidator)
async def create_user(user: UserValidator, db: db_dependency):
    user_dict = user.dict()
    db_user = User(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserValidator)
async def read_user(user_id: int, db: db_dependency):
    user = db.query(User).filter(User.Userid == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserValidator)
async def update_user(user_id: int, user: UserValidator, db: db_dependency):
    db_user = db.query(User).filter(User.Userid == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.dict().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", response_model=UserValidator)
async def delete_user(user_id: int, db: db_dependency):
    db_user = db.query(User).filter(User.Userid == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return db_user

