from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.core import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Repositório base genérico com operações fundamentais de persistência."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Busca um registro pela chave primária."""
        return self.db.get(self.model, id)

    def get_all(self) -> List[ModelType]:
        """Retorna todos os registros do modelo."""
        return self.db.query(self.model).all()

    def create(self, instance: ModelType) -> ModelType:
        """Adiciona e persiste um novo registro no banco de dados."""
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        """Remove um registro persistido."""
        self.db.delete(instance)
        self.db.commit()

    def commit(self) -> None:
        """Executa o commit das alterações pendentes na sessão."""
        self.db.commit()

    def refresh(self, instance: ModelType) -> None:
        """Atualiza os atributos da instância a partir do banco de dados."""
        self.db.refresh(instance)
