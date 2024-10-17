from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utilities.database import SessionLocal
from models.user import Review
from validator.review import ReviewValidator
from typing import List, Annotated

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
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

# Create Review
@router.post("/", response_model=ReviewValidator)
async def create_review(review: ReviewValidator, db: db_dependency):
    review_dict = review.dict()
    db_review = Review(**review_dict)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

# Read Review by ID
@router.get("/{review_id}", response_model=ReviewValidator)
async def read_review(review_id: int, db: db_dependency):
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

# Read All Reviews with Pagination
@router.get("/", response_model=List[ReviewValidator])
async def read_reviews(db: db_dependency, skip: int = 0, limit: int = 10):
    reviews = db.query(Review).offset(skip).limit(limit).all()
    return reviews

# Update Review
@router.put("/{review_id}", response_model=ReviewValidator)
async def update_review(review_id: int, review: ReviewValidator, db: db_dependency):
    db_review = db.query(Review).filter(Review.review_id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    for key, value in review.dict().items():
        setattr(db_review, key, value)
    db.commit()
    db.refresh(db_review)
    return db_review

# Delete Review
@router.delete("/{review_id}", response_model=ReviewValidator)
async def delete_review(review_id: int, db: db_dependency):
    db_review = db.query(Review).filter(Review.review_id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(db_review)
    db.commit()
    return db_review