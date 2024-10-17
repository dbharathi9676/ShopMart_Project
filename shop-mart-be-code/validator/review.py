from pydantic import BaseModel, Field, condecimal
from typing import Optional
from datetime import datetime

class ReviewValidator(BaseModel):
    Reviewid: int
    userid: int
    productid: int
    rating: condecimal(gt=0, le=5)  # Rating should be between 1 and 5
    comment: Optional[str] = None
    review_date: datetime = Field(default_factory=datetime.utcnow)
