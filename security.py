from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from config import settings
import logging

logger = logging.getLogger(__name__)


SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM
password_context = PasswordHash.recommended()
oatuh2_schema = OAuth2PasswordBearer(tokenUrl="user/token")


def get_password_hash(password: str):
    return password_context.hash(password)

def verify_password(password: str, hash_password: str):
    return password_context.verify(password, hash_password)

DUMMY_HASH = password_context.hash("dummy_password")
def dummy_verify():
    verify_password("wrong_password", DUMMY_HASH)

def create_access_token(user_id: int, expire_time: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    expire_date = datetime.now(timezone.utc) + expire_time
    info = {"sub": str(user_id), "exp": expire_date}
    encoded_jwt = jwt.encode(info, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        return None