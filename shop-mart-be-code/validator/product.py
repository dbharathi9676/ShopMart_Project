from pydantic import BaseModel, Field, HttpUrl
from typing import Optional

class ProductValidator(BaseModel):
    id: int
    productname: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_name: str = Field(..., min_length=1, max_length=100)
    userID: int
    image_url: Optional[HttpUrl] = None
