from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utilities.database import SessionLocal
from models.user import Payment
from validator.payment import PaymentValidator
from typing import List, Annotated

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
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

@router.post("/", response_model=PaymentValidator)
async def create_payment(payment: PaymentValidator, db: db_dependency):
    payment_dict = payment.dict()
    db_payment = Payment(**payment_dict)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("/{payment_id}", response_model=PaymentValidator)
async def read_payment(payment_id: int, db: db_dependency):
    payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/", response_model=List[PaymentValidator])
async def read_payments(db: db_dependency, skip: int = 0, limit: int = 10):
    payments = db.query(Payment).offset(skip).limit(limit).all()
    return payments


@router.put("/{payment_id}", response_model=PaymentValidator)
async def update_payment(payment_id: int, payment: PaymentValidator, db: db_dependency):
    db_payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    for key, value in payment.dict().items():
        setattr(db_payment, key, value)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.delete("/{payment_id}", response_model=PaymentValidator)
async def delete_payment(payment_id: int, db: db_dependency):
    db_payment = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if db_payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(db_payment)
    db.commit()
    return db_payment