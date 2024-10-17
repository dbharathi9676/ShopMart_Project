from utilities.database import engine, Base
from models.user import User



def create():
    Base.metadata.create_all(bind=engine)