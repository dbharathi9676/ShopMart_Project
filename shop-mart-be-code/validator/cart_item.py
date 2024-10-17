from pydantic import BaseModel, Field


class CartItemValidator(BaseModel):
    cartID: int
    userID: int
    productID: int
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
