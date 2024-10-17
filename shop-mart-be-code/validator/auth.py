import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException, status, Depends
from typing import Optional
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from utilities.constant import GOOGLE_CLIENT_ID, ALLOWED_DOMAINS, \
    JWT_SECRET_KEY, JWT_EXPIRY_WINDOW_IN_HOURS, JWT_ENCODING_ALGORITHM
import logging
import utilities.logger as Logger
from models.user import User
from models import Session

error_logger = Logger.get_logger('error', logging.ERROR)
info_logger = Logger.get_logger('info', logging.INFO)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_email_from_token(auth_token):
    try:
        decoded_token = jwt.decode(jwt=auth_token, key=JWT_SECRET_KEY, algorithms=JWT_ENCODING_ALGORITHM)
        if decoded_token and decoded_token['email']:
            return decoded_token['email']
        else:
            error_logger.error(f'Invalid token or token')
    except ExpiredSignatureError as e:
        error_logger.error(f'Token is expired.')
    except InvalidTokenError as e:
        error_logger.error(f'Token is invalid. Error: {e}')
    except Exception as e:
        error_logger.exception(f'Exception occured in get_email_from_token. Error: {e}')
    return None


def verify_jwt_token(auth_token, email):
    is_verified_token = False
    try:
        decoded_token = jwt.decode(jwt=auth_token, key=JWT_SECRET_KEY, algorithms=JWT_ENCODING_ALGORITHM)
        if decoded_token and decoded_token['email'] == email:
            is_verified_token = True
        else:
            error_logger.error(f'Invalid token or token does not belong to this email: {email}')
    except ExpiredSignatureError as e:
        error_logger.error(f'Token is expired.')
    except InvalidTokenError as e:
        error_logger.error(f'Token is invalid. Error: {e}')
    except Exception as e:
        error_logger.exception(f'Exception occured in verify_jwt_token. Error: {e}')
    return is_verified_token


def get_user_domain_from_email(email):
    try:
        if not email:
            return None
        username, domain = email.split('@')
        return domain
    except Exception as e:
        print(f'Exception occured in get_user_domain_from_email. Error: {e}')


def validate_oauth_token(outh_token):
    token_dict = {}
    try:
        if not outh_token:
            token_dict['error'] = 'Oauth token can not be null.'
            return token_dict

        verified_token_details = id_token.verify_oauth2_token(
            outh_token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        logging_user_domain = get_user_domain_from_email(verified_token_details.get('email'))
        print("logging_user_domain:", logging_user_domain)
        if not logging_user_domain in ALLOWED_DOMAINS:
            token_dict['error'] = f'Domain {logging_user_domain} is not allowed.'

        token_dict['user_details'] = {
            'name': f'{verified_token_details.get("given_name", "")} {verified_token_details.get("family_name", "")}',
            'email': verified_token_details.get('email'),
            'picture': verified_token_details.get('picture')
        }
    except Exception as e:
        error_logger.exception(f'Exception occured while validating oauth token. Error: {e}')
        token_dict['error'] = 'Invalid oauth token.'
    return token_dict

def create_jwt_token(email):
    token_dict = {'access_token': None}
    try:
        expiration_time = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_WINDOW_IN_HOURS)
        payload = {'email': email, 'exp': expiration_time}
        access_token = jwt.encode(payload=payload, key=JWT_SECRET_KEY, algorithm=JWT_ENCODING_ALGORITHM)
        token_dict['access_token'] = access_token
    except Exception as e:
        error_logger.exception('Exception occured while validating oauth token.')
        token_dict['error'] = f'Failed to create JWT token for user: {email}'
    return token_dict


def login_user(email, oauth_token):
    try:
        validated_token_dict = validate_oauth_token(oauth_token)
        if 'error' in validated_token_dict:
            return {'message': validated_token_dict['error'], 'status_code': 401}
        else:

            user_details = validated_token_dict.get("user_details")
            if user_details and user_details.get("email") == email:
                access_token_dict = create_jwt_token(email)
                if 'error' in access_token_dict:
                    raise Exception(access_token_dict['error'])
                return {'data': {'user_details': validated_token_dict['user_details'], **access_token_dict},
                        'status_code': 200}
            else:
                return {'message': "Email didn't match", 'status_code': 401}
    except Exception as e:
        error_logger.exception(f'Exception occured in login. Error: {e}')
        return {'message': f'Failed to login user: {email}', 'status_code': 401}


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)




def authenticate_user(username: str, password: str):
    try:
        session = Session()
        user = session.query(User).filter(User.username == username).first()

        if not user:
            error_logger.error(f'User not found for username: {username}')
            return None  

        if not verify_password(password, user.hashed_password):
            error_logger.error(f'Password verification failed for user: {username}')
            return {"authenticated": False}  
        return user
    except Exception as e:
        error_logger.exception(f'Exception occurred in authenticate_user. Error: {e}')
        return {"error": str(e)}



def create_access_token(username: str, user_id: int, email: str,
                        expires_delta: Optional[timedelta] = None):
    encode = {"user": username, "user_id": user_id, "email": email}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, JWT_SECRET_KEY, algorithm=JWT_ENCODING_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ENCODING_ALGORITHM])
        username: str = payload.get("user")
        user_id: int = payload.get("user_id")
        email: str = payload.get('email')
        # Ensure that all required fields are present in the payload
        if email is None:
            raise get_user_exception()

        return {'username': username, 'user_id': user_id,'email': email}
    except jwt.ExpiredSignatureError:
        # Handle token expiration
        raise get_user_exception(detail="Token has expired")
    except jwt.InvalidTokenError:
        # Handle invalid token
        raise get_user_exception(detail="Invalid token")
    except Exception as e:
        # Log other exceptions
        error_logger.exception(f'Exception occurred in get_current_user. Error: {e}')
        raise get_user_exception()

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        session = Session()
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ENCODING_ALGORITHM])
        username: str = payload.get("user")
        user_id: int = payload.get("user_id")
        email: str = payload.get('email')
        # Ensure that all required fields are present in the payload
        if email is None:
            raise get_user_exception()

        if user_id is None:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                raise get_user_exception()

            user_id = user.id

        return {'username': username, 'user_id': user_id, 'email': email}
    except jwt.ExpiredSignatureError:
        # Handle token expiration
        raise get_user_exception(detail="Token has expired")
    except jwt.InvalidTokenError:
        # Handle invalid token
        raise get_user_exception(detail="Invalid token")
    except Exception as e:
        # Log other exceptions
        error_logger.exception(f'Exception occurred in get_current_user. Error: {e}')
        raise get_user_exception()


def get_user_exception(detail: str = "Could not validate credentials"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def token_exception():
    token_exception_reponse = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}

    )
    return token_exception_reponse

async def send_notification(email: str, subject: str, body: str):
    sender_email =  "admin@maangtechnologies.com"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = sender_email
    smtp_password = "yxlw dmcb lkod luob"    # Replace with your actual SMTP password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, email, message.as_string())
