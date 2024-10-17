from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utilities.database import SessionLocal
from models.user import CartItem
from validator.cart_item import CartItemValidator
from typing import List, Annotated

router = APIRouter(
    prefix="/cartitems",
    tags=["cartitems"],
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

# Create CartItem
@router.post("/", response_model=CartItemValidator)
async def create_cartitem(cartitem: CartItemValidator, db: db_dependency):
    cartitem_dict = cartitem.dict()
    db_cartitem = CartItem(**cartitem_dict)
    db.add(db_cartitem)
    db.commit()
    db.refresh(db_cartitem)
    return db_cartitem

# Read CartItem by ID
@router.get("/{cart_id}", response_model=CartItemValidator)
async def read_cartitem(cart_id: int, db: db_dependency):
    cartitem = db.query(CartItem).filter(CartItem.cart_id == cart_id).first()
    if cartitem is None:
        raise HTTPException(status_code=404, detail="CartItem not found")
    return cartitem

# Read All CartItems with Pagination
@router.get("/", response_model=List[CartItemValidator])
async def read_cartitems(db: db_dependency, skip: int = 0, limit: int = 10):
    cartitems = db.query(CartItem).offset(skip).limit(limit).all()
    return cartitems

# Update CartItem
@router.put("/{cart_id}", response_model=CartItemValidator)
async def update_cartitem(cart_id: int, cartitem: CartItemValidator, db: db_dependency):
    db_cartitem = db.query(CartItem).filter(CartItem.cart_id == cart_id).first()
    if db_cartitem is None:
        raise HTTPException(status_code=404, detail="CartItem not found")
    for key, value in cartitem.dict().items():
        setattr(db_cartitem, key, value)
    db.commit()
    db.refresh(db_cartitem)
    return db_cartitem

# Delete CartItem
@router.delete("/{cart_id}", response_model=CartItemValidator)
async def delete_cartitem(cart_id: int, db: db_dependency):
    db_cartitem = db.query(CartItem).filter(CartItem.cart_id == cart_id).first()
    if db_cartitem is None:
        raise HTTPException(status_code=404, detail="CartItem not found")
    db.delete(db_cartitem)
    db.commit()
    return db_cartitem