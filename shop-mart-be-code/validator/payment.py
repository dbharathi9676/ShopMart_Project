from pydantic import BaseModel, Field
from datetime import datetime

class PaymentValidator(BaseModel):
    paymentId: int
    orderid: int
    payment_date: datetime = Field(default_factory=datetime.utcnow)
    payment_method: str = Field(..., min_length=1, max_length=50)
    payment_amount: float = Field(..., gt=0)
