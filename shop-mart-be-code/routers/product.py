from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from utilities.database  import SessionLocal
from models.user import Product
from validator.product import ProductValidator
from typing import List, Annotated

router = APIRouter(
    prefix="/products",
    tags=["products"],
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


@router.post("/", response_model=ProductValidator)
async def create_product(product: ProductValidator, db: db_dependency):
    product_dict = product.dict()

    # Convert HttpUrl or Url object to string
    product_dict['image_url'] = str(product_dict.get('image_url', ''))

    db_product = Product(**product_dict)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/{product_id}")
async def read_product(product_id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/")
async def read_products(db: db_dependency, skip: int = 0, limit: int = 10):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.put("/{product_id}", response_model=ProductValidator)
async def update_product(product_id: int, product: ProductValidator, db: db_dependency):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: db_dependency):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return db_product
