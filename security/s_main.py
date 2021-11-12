from datetime import datetime, timedelta
from typing import Optional, Union, Literal
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from security.s_scheme import TokenData
from scheme import UserInDB
from models import User
from pydantic import ValidationError
from pony.orm import db_session

#  from main import SECRET_KEY

# TODO: add .env

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes={"admin": "Read information about the current user.",
                                                               "user": "Read items."})


def verify_password(plain_password, hashed_password):  # проверяет правильность пароля, True/False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):  # хэширует пароль
    return pwd_context.hash(password)


def get_user(user_name: str) -> Union[UserInDB, str]:  # ------------
    with db_session:
        if User.exists(name=user_name):  # если юзер есть в бд, то выводим его
            user = User.get(name=user_name)
            return UserInDB.from_orm(user)
        else:
            return 'пользователя с таким именем не существует'


def authenticate_user(user_name: str, password: str, scope: list) -> Union[UserInDB, Literal[False]]:  # --------------
    user = get_user(user_name)
    print(user)
    print(scope)
    if isinstance(user, str):
        return False
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    if len(scope) > 1:
        return False
    if user.admin_rights is True and scope[0] == 'user':
        return False
    if user.admin_rights is False and scope[0] == 'admin':
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):  # ставит метку
    from main import SECRET_KEY
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    from main import SECRET_KEY
    # где-то в ф должна быть проверка на админа
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # tokenUrl and scopes + s_k + alg
        username: str = payload.get("sub")  # ?
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])  # то, что отметили галочкой
        token_data = TokenData(name=username, scopes=token_scopes)  # !
    except (JWTError, ValidationError):
        raise credentials_exception
    user = get_user(token_data.name)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Недостаточно прав",
                                headers={"WWW-Authenticate": authenticate_value})
    return user


async def get_current_active_admin(current_user: User = Security(get_current_user, scopes=["admin"])):  # UserInDB
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive admin")
    return current_user


async def get_current_active_user(current_user: User = Security(get_current_user, scopes=["user"])):  # UserInDB
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active(current_user: User = Security(get_current_user)):  # UserInDB
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive admin")
    return current_user