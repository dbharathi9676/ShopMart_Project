from typing import Optional
import os
# from infra.apscheduler import start_scheduler, stop_scheduler
# from infra.middleware import InputFilterMiddleware
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import user
from app import create_tables
from routers import password
from routers import product
from routers import user
from routers import cart_item
from routers import payment
from routers import order
from routers import review


create_tables.create() #This will create the tables automatically, first create database(create the schema within db if exists.)

app = FastAPI(debug=True)
#env specific

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(InputFilterMiddleware)

#app.add_middleware(InputFilterMiddleware)


app.include_router(user.router)

app.include_router(password.router)


app.include_router(product.router)


app.include_router(user.router)

app.include_router(payment.router)

app.include_router(order.router)

app.include_router(review.router)

app.include_router(cart_item.router)
# models.Base.metadata.create_all(bind=engine)


# if __name__ == "__main__":

#     start_scheduler()
#     uvicorn.run("main:app", host="0.0.0.0", port=8400, log_level="debug",reload=True)
