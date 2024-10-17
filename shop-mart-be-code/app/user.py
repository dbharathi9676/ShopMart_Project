
import traceback
from typing import Annotated
from sqlalchemy.orm import Session

import logging
import json
from typing import Optional
from fastapi import Request, Response, status, Depends, APIRouter, HTTPException
from stripe import AuthenticationError
from models import user
from validator.common_validator import CreateUser, StudentDetails
from validator.auth import get_current_user, get_password_hash,authenticate_user, token_exception, create_access_token, timedelta
from starlette.responses import JSONResponse
from models import Session
from models.user import User
from validator import common_validator, user, auth
from validator import user
from utilities.constant import PREFIX_URL
import utilities.logger as Logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi.security import OAuth2PasswordRequestForm
error_logger = Logger.get_logger('error', logging.ERROR)
info_logger = Logger.get_logger('info', logging.INFO)

router = APIRouter(prefix='', tags=["auth"])
def get_db():
    db=Session()
    try:
        yield db
    finally:
        if db:
            db.close()
db_dependency = Annotated[Session, Depends(get_db)]
def get_users(email):
    session = None
    try:
        session = Session()
        result_set = session.query(User).filter(User.email == email)
        result_set_count = result_set.count()
        result_set = result_set.all()
        if result_set_count > 0:
            for db_ in result_set:
                if db_.access == 'super':
                    return True
                else:
                    return False
        else:
            return None
    except Exception as err:
        return None
    finally:
        if session:
            session.close()

@router.post(PREFIX_URL + "/social-login")
async def create_user(request_context: Request, user: user.UserValidator, response: Response):
    session = None
    try:
        session = Session()
        email = user.email
        access = "normal_user"
        username = user.username
        oauth_token = user.oauth_token
        mobile_number = user.mobile_number if hasattr(User, 'mobile_number') else None
        address_line1=user.address_line1 if hasattr(User, 'address_line1') else None
        address_line2 = user.address_line2 if hasattr(User, 'address_line2') else None
        postcode = user.postcode if hasattr(User, 'postcode') else None
        student_details_json = json.dumps(user.studentDetails.dict()) if user.studentDetails else None
        parent_details_json=json.dumps(user.parentDetails.dict()) if user.parentDetails else None



        data = auth.login_user(email, oauth_token)
        if data.get("status_code") == 200:
            result_set = session.query(User).filter(User.email == email)
            result_set_count = result_set.count()
            result_set = result_set.all()
            if result_set_count == 0:
                db_ = User(email=email, username=username,student_details=student_details_json,parent_details=parent_details_json,address_line1=address_line1,address_line2=address_line2,postcode=postcode,mobile_number=mobile_number)
                session.add(db_)
                session.commit()
                session.refresh(db_)
                response.status_code = status.HTTP_201_CREATED
                info_logger.info(f'User added: {email}')
            else:
                access = get_users(email)

        data["normal_user"] = access
        return data
    except Exception as err:
        error_logger.exception(f'Exception occurred in create_user. Error: {err}')
        return JSONResponse({"error_code": "create_user_api_failed",
                             "message": "Technical Error occurred while storing the create_user"}, status_code=500)
    finally:
        if session:
            session.close()


@router.post(PREFIX_URL + "/new-user")
async def createnew_user(db: db_dependency, CreateUser: CreateUser):
    existing_user = db.query(User).filter(User.username == CreateUser.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    existing_email = db.query(User).filter(User.email == CreateUser.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    try:
        hashed_password = get_password_hash(CreateUser.password)
        student_details_json = json.dumps(CreateUser.studentDetails.dict()) if CreateUser.studentDetails else None
        parent_details_json = json.dumps(CreateUser.parentDetails.dict()) if CreateUser.parentDetails else None
        new_user = User(
            username=CreateUser.username,
            email=CreateUser.email,
            hashed_password=hashed_password,
            student_details=json.loads(student_details_json),
            parent_details=json.loads(parent_details_json),
            mobile_number=CreateUser.mobile_number,
            address_line1=CreateUser.address_line1,
            address_line2=CreateUser.address_line2,
            postcode=CreateUser.postcode,
            country=CreateUser.country,
            city=CreateUser.city,
            created_date=CreateUser.created_date
        )
        db.add(new_user)
        db.commit()
        return {"message": "Your registration was successful.",
                "status_code": status.HTTP_200_OK}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable entity. Invalid data provided.")
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error. Please try again later.")

@router.get(PREFIX_URL + "/users")
async def get_user_all( page: Optional[int] = 0, size: Optional[int] = 10000):
    session = None
    access = None
    try:
        if page != 0:
            # index starts from zero,req page is 1 means index 0.
            page = page - 1
        session = Session()
        result_set = session.query(User).order_by(User.created_date.desc()).offset(
            page * size).limit(size).all()
        if result_set:
            return {"data": result_set, "admin": access, "status_code": 200}
        else:
            return JSONResponse({"detail": "NOT_FOUND"}, status_code=404)
    # else:
    #    return {"Authentication Failed."}
    except Exception as err:
        error_logger.exception(f'Exception occured in get_user_all. Error: {err}')
        return JSONResponse({"error_code": "get_user_api_failed",
                             "message": "Technical Error occurred while retrieving the user"}, status_code=500)
    finally:
        if session:
            session.close()
@router.post(PREFIX_URL + "/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        print(user)

        if user is None:
            return {"message":"User not found","status_code":status.HTTP_404_NOT_FOUND}

        if isinstance(user, dict) and user.get('authenticated', False) is False:
            return {"message":"Invalid username or password","status_code":status.HTTP_400_BAD_REQUEST}
    
        if isinstance(user, dict) and "error" in user:
            return {"message":"Internal server error. Please try again later","status_code":status.HTTP_500_INTERNAL_SERVER_ERROR}
    
        token_expires = timedelta(minutes=15)
        token = create_access_token(user.email,user.username, user.id, expires_delta=token_expires)

        return {"access_token": token, "token_type": "Bearer"}
    except ValueError as ve:
        error_logger.exception(f'ValueError occurred: {ve}')
        raise HTTPException(status_code=422, detail="Unprocessable entity,Invalid data provided.")
    except Exception as e:
        error_logger.exception(f'Exception occurred in login_for_access_token. Error: {e}')
        raise HTTPException(status_code=401, detail="Unauthorized access. Please log in.")
        
@router.delete(PREFIX_URL + "/user/{email}")
async def delete_user(email: str):

    session = Session()
    user_model = session.query(User).filter(User.email == email).first()

    if not user_model:
        return JSONResponse({"detail": "USER_NOT_FOUND"}, status_code=404)
    try:
        session.query(User).filter(User.email==email).delete()
        session.commit()
        return JSONResponse({"detail": "success"})
    except SQLAlchemyError as db_error:
        session.rollback()
        error_logger.exception(f'SQLAlchemyError occurred in delete_user. Error: {db_error}')
        return JSONResponse({"error_code": "delete_user_db_error",
                             "message": f"Database Error occurred while deleting the user. Error: {db_error}"},
                            status_code=500)
    except Exception as general_error:
        error_logger.exception(f'Exception occurred in delete_user. Error: {general_error}')
        return JSONResponse({"error_code": "delete_user_api_failed",
                             "message": f"Technical Error occurred while deleting the user. Error: {general_error}"},
                            status_code=500)
    finally:
        if session:
            session.close()
@router.get(PREFIX_URL + "/user_by_id")
async def get_user_by_id(id:int,page: Optional[int] = 0, size: Optional[int] = 20):

    session = Session()
    try:
        users = session.query(User).filter(User.id == id).all()

        if not users:
            return JSONResponse({"detail": "NO_USERS_FOUND"}, status_code=404)

        return {"message": "successful", "data": users, "status": status.HTTP_200_OK}
    except Exception as e:
        error_logger.exception(f'Exception occurred in get user by id. Error: {e}')
        raise HTTPException(status_code=500, detail="internal server error")
    finally:
        if session:
            session.close()
