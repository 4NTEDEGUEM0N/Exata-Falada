from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os
from settings import settings

DATABASE_URL = settings.DATABASE_URL

db = create_engine(DATABASE_URL)

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def upgrade_db():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(base_dir, "alembic.ini")
    
    alembic_cfg = Config(ini_path)
    alembic_cfg.set_main_option('sqlalchemy.url', DATABASE_URL)
    
    print("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations successfully applied!")
    create_first_admin()


def create_first_admin():
    from models.user_model import UserModel
    from security import get_password_hash

    db = SessionLocal() 

    try:
        admin_exists = db.query(UserModel).filter(UserModel.admin == True).first()

        if admin_exists:
            print("Admin already exists.")
            return
        
        admin_username = settings.ADMIN_USER
        admin_password = settings.ADMIN_PASSWORD

        if not admin_username or not admin_password:
            print("Invalid admin credentials")
            return

        new_admin = UserModel(
            username=admin_username, 
            password=get_password_hash(admin_password), 
            admin=True
        )
        
        db.add(new_admin)
        db.commit()
        print(f"Admin '{admin_username}' created.")
        
    except Exception as e:
        db.rollback()
        print(f"Error on admin creation: {e}")
        
    finally:
        db.close()