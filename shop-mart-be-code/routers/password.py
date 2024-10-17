from fastapi import APIRouter,Depends,HTTPException,Path,status
from models import Session
from models.user import User
from datetime import datetime,timedelta
from validator.auth import send_notification, verify_password
import random
import utilities.logger as Logger
import logging
import string
from validator.auth import get_password_hash
from typing import Annotated
router = APIRouter(
    prefix ='/password',
    tags=['password'],
    responses={401: {"detail": "Not authorized"}}
)


error_logger = Logger.get_logger('error', logging.ERROR)
info_logger = Logger.get_logger('info', logging.INFO)



def get_db():
    db=Session()
    try:
        yield db
    finally:
        if db:
            db.close()
db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/forgot-password")
async def forgot_password(email: str, db: db_dependency):
    info_logger.info(f"User with email {email} requested for password reset")
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Generate a random OTP
            otp = "".join(random.choices(string.digits, k=6))
            user.otp = otp
            user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
            db.commit()
            # Send the OTP to the user via email
            subject = "Password Reset OTP"
            body = f"Your OTP for password reset is: {otp}. This OTP is valid for 10 minutes."
            await send_notification(email, subject, body)
            return {"message": "OTP has been sent to your email address",
                "status_code": status.HTTP_201_CREATED}
        else:
            return {"message":"Email address not found","status_code":status.HTTP_404_NOT_FOUND}
    except ValueError as ve:
        error_logger.exception(f'ValueError occurred: {ve}')
        raise HTTPException(status_code=422, detail="Unprocessable entity,Invalid data provided.")  
    except Exception as e: 
        error_logger.error(f"Error occurred in /forgot-password API while generating OTP for user with email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db:
            db.close()


# @router.post("/check-otp")
# async def check_otp(otp:str,db: db_dependency):
#     info_logger.info(f"User is checking OTP: {otp}")
#     try:
#         user = db.query(User).filter(User.otp==otp).first()
#         if user and user.otp_expires > datetime.utcnow():
#             return {"message": "OTP is valid"}
#         else:
#             return {"message":"Invalid or expired OTP","status_code":status.HTTP_400_BAD_REQUEST}

#     except Exception as e:       
#         error_logger.error(f"Error occurred in /check-otp API while checking OTP: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")
#     finally:
#         if db:
#             db.close()
@router.post("/check-otp")
async def check_otp(otp:str,db: db_dependency):
    info_logger.info(f"User is checking OTP: {otp}")
    
    try:
        user = db.query(User).filter(User.otp == otp).first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP. Please try again.")
        
        if user.otp_expires <= datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OTP expired or invalid. Please request a new one.")
        
        return {"message": "OTP is valid", "status_code": status.HTTP_200_OK}

    except HTTPException as e:
        raise e
    except Exception as e:
        error_logger.error(f"Error occurred in /check-otp API while checking OTP: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred. Please try again later.")


@router.put("/update-password")
async def update_password(new_password: str, email: str, old_password: str, db:db_dependency):
    info_logger.info(f"User with email {email} is updating password")
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if not verify_password(old_password, user.hashed_password):
                return {"message": "Old password is incorrect","status_code":status.HTTP_401_UNAUTHORIZED}
            if verify_password(new_password, user.hashed_password):
                return {"message": "Invalid request. The new password cannot be the same as the old password","status_code":status.HTTP_409_CONFLICT}
                
            user.hashed_password = get_password_hash(new_password)
            user.otp = None
            user.otp_expires = None
            db.commit()
            return {"message": "Password updated successfully","status_code":status.HTTP_201_CREATED}
        else:
            return {"message": "User not found","status_code":status.HTTP_400_BAD_REQUEST}
    except Exception as e:
        error_logger.error(f"Error occurred in /update-password API while updating password for user with email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if db:
            db.close()