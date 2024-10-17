
from pydantic import BaseModel,EmailStr,validator
from typing import Optional
from datetime import date
class StudentDetails(BaseModel):
    firstName: str
    lastName: str

class ParentDetails(BaseModel):
    parent_first_name:str
    parent_last_name : str

class CreateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    mobile_number:str
    studentDetails: Optional[StudentDetails]= None
    parentDetails:Optional[StudentDetails]= None
    address_line1: str
    address_line2: Optional[str] = None
    postcode: str
    created_date:date
    country:str
    city:str
    @validator('postcode')
    def remove_spaces_from_postcode(cls, v):
        # Remove leading and trailing spaces from the pin code
        return v.strip()