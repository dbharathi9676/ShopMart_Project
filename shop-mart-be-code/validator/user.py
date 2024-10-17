
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import enum

class UserType(str, enum.Enum):
    customer = "customer"
    vendor = "vendor"

class UserValidator(BaseModel):
    username: str = Field(..., example="user123", min_length=3)
    password: str = Field(..., example="password123", min_length=6)
    email: EmailStr = Field(..., example="user@example.com")
    fullname: str = Field(..., example="John Doe")
    address: Optional[str] = Field(None, example="123 Main St")
    phonenumber: Optional[str] = Field(None, example="555-1234")
    Usertype: UserType = Field(..., example="customer")
    storename: Optional[str] = Field(None, example="Store Name")
    storeaddress: Optional[str] = Field(None, example="Store Address")

    class Config:
        orm_mode = True




