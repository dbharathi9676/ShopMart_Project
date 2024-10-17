from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class OrderValidator(BaseModel):
    orderId: int
    userid: int
    order_date: datetime = Field(default_factory=datetime.utcnow)
    status: OrderStatus
