from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utilities.database import Base
import enum

# Enum for UserType
class UserType(enum.Enum):
    customer = "customer"
    vendor = "vendor"

# Enum for Order Status
class OrderStatus(enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"

class User(Base):
    __tablename__ = 'users'

    Userid = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    fullname = Column(String, nullable=False)
    address = Column(String, nullable=True)
    phonenumber = Column(String, nullable=True)
    Usertype = Column(Enum(UserType), nullable=False)
    storename = Column(String, nullable=True)
    storeaddress = Column(String, nullable=True)

    cart_items = relationship("CartItem", back_populates="user")
    products = relationship("Product", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    productname = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    category_name = Column(String, nullable=False)
    userID = Column(Integer, ForeignKey('users.Userid'), nullable=False)
    image_url = Column(String, nullable=True)

    user = relationship("User", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")

    # is_active = Column(Boolean, default=True)  # Default value for is_active
    # created_by = Column(String)
    # modified_by = Column(String)
    # created_date = Column(DateTime(timezone=False), server_default=func.now())
    # modified_date = Column(DateTime(timezone=False), onupdate=func.now())

class CartItem(Base):
    __tablename__ = 'cartitems'

    cartID = Column(Integer, primary_key=True, index=True)
    userID = Column(Integer, ForeignKey('users.Userid'), nullable=False)
    productID = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class Review(Base):
    __tablename__ = 'reviews'

    Reviewid = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey('users.Userid'), nullable=False)
    productid = Column(Integer, ForeignKey('products.id'), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    review_date = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

class Order(Base):
    __tablename__ = 'orders'

    orderId = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey('users.Userid'), nullable=False)
    order_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)

    user = relationship("User", back_populates="orders")
    payments = relationship("Payment", back_populates="order")

class Payment(Base):
    __tablename__ = 'payments'

    paymentId = Column(Integer, primary_key=True, index=True)
    orderid = Column(Integer, ForeignKey('orders.orderId'), nullable=False)
    payment_date = Column(DateTime, default=func.now(), nullable=False)
    payment_method = Column(String, nullable=False)
    payment_amount = Column(Float, nullable=False)

    order = relationship("Order", back_populates="payments")





