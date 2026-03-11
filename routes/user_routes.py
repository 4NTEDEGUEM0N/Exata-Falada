from fastapi import APIRouter, Depends, HTTPException, status
from models.user_model import UserModel
from database import get_db
from sqlalchemy.orm import Session
from security import get_password_hash, verify_password, decode_token, oatuh2_schema, create_access_token, dummy_verify
from pydantic import BaseModel, ConfigDict
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm

user_router = APIRouter(prefix="/user", tags=["user"])

class UserCreate(BaseModel):
    username: str
    password: str
    admin: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    

@user_router.post("/token", response_model=TokenResponse)
async def loginToken(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    else:
        access_token = create_access_token(user.id)
        return TokenResponse(access_token=access_token, token_type="bearer")

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oatuh2_schema)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    user_id = int(user_id)
    user = db.get(UserModel, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    
    return user

@user_router.post("/signup", response_model=UserResponse)
async def create_user(user_schema: UserCreate, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    user = db.query(UserModel).filter(UserModel.username == user_schema.username).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    else:
        hash_password = get_password_hash(user_schema.password)
        user_data = user_schema.model_dump(exclude_unset=True)
        user_data["password"] = hash_password
        new_user = UserModel(**user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

@user_router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


def authenticate_user(username: str, password: str, db: Session):
    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        dummy_verify()
        return None
    elif not verify_password(password, user.password):
        return None

    return user