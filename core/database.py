from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
import os
import logging
import sys
from .config import settings

logger = logging.getLogger(__name__)

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
    # Caminho raiz da aplicação para localizar o alembic.ini
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ini_path = os.path.join(base_dir, "alembic.ini")
    
    if sys.platform != "win32":
        import fcntl
        lock_file = os.path.join(base_dir, "alembic_upgrade.lock")
        fd = open(lock_file, "w")
        try:
            # Tenta adquirir um lock exclusivo sem bloquear (non-blocking)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            logger.info("Database is being upgraded by another worker. Waiting...")
            # Bloqueia esperando o outro worker terminar e liberar o lock
            fcntl.flock(fd, fcntl.LOCK_EX)
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
            return
            
        try:
            _run_upgrade(ini_path)
        finally:
            # Libera o lock após terminar a migração
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
    else:
        # No Windows (desenvolvimento), geralmente usamos uvicorn com reload (1 worker)
        _run_upgrade(ini_path)

def _run_upgrade(ini_path):
    alembic_cfg = Config(ini_path)
    alembic_cfg.set_main_option('sqlalchemy.url', DATABASE_URL)
    alembic_cfg.attributes["configure_logger"] = False
    
    logger.info("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations successfully applied!")
    create_first_admin()

def create_first_admin():
    from models.user_model import UserModel
    from .security import get_password_hash

    db = SessionLocal() 

    try:
        admin_exists = db.query(UserModel).filter(UserModel.admin == True).first()

        if admin_exists:
            logger.info("Admin already exists.")
            return
        
        admin_username = settings.ADMIN_USER
        admin_password = settings.ADMIN_PASSWORD

        if not admin_username or not admin_password:
            logger.warning("Invalid admin credentials")
            return

        new_admin = UserModel(
            username=admin_username, 
            password=get_password_hash(admin_password), 
            admin=True
        )
        
        db.add(new_admin)
        db.commit()
        logger.info(f"Admin '{admin_username}' created.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error on admin creation: {e}")
        
    finally:
        db.close()
