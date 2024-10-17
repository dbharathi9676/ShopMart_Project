from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utilities.database import SessionLocal
from models.user import Order
from validator.order import OrderValidator
from typing import List, Annotated

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
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


@router.post("/", response_model=OrderValidator)
async def create_order(order: OrderValidator, db: db_dependency):
    order_dict = order.dict()
    db_order = Order(**order_dict)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/{order_id}", response_model=OrderValidator)
async def read_order(order_id: int, db: db_dependency):
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/", response_model=List[OrderValidator])
async def read_orders(db: db_dependency, skip: int = 0, limit: int = 10):
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

@router.put("/{order_id}", response_model=OrderValidator)
async def update_order(order_id: int, order: OrderValidator, db: db_dependency):
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    for key, value in order.dict().items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}", response_model=OrderValidator)
async def delete_order(order_id: int, db: db_dependency):
    db_order = db.query(Order).filter(Order.order_id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(db_order)
    db.commit()
    return db_order