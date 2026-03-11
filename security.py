from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from config import settings


SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oatuh2_schema = OAuth2PasswordBearer(tokenUrl="user/token")


def get_password_hash(senha: str):
    return bcrypt_context.hash(senha)

def verify_password(senha: str, senha_hash: str):
    return bcrypt_context.verify(senha, senha_hash)

def dummy_verify():
    bcrypt_context.dummy_verify()

def create_access_token(user_id: int, expire_time: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    expire_date = datetime.now(timezone.utc) + expire_time
    info = {"sub": str(user_id), "exp": expire_date}
    encoded_jwt = jwt.encode(info, SECRET_KEY, ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None