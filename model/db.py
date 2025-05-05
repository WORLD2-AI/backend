from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict
# database gsn
DATABASE_URL = 'mysql+pymysql://root:123456@localhost:3306/character_db'

engine = create_engine(DATABASE_URL, pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20
)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    return db
class BaseModel():
    def __init__(self, **kwargs):
        self.model_class = self.get_model_class()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_model_class(self):
        for base in self.__class__.__mro__:
            if hasattr(base, "__tablename__"):
                return base
        raise AttributeError("Model class not found for the current instance.")

    def get_session(self):
        return get_db()  

    def first(self, filters: Optional[Dict] = None) -> object:
        with self.get_session() as session:
            query = session.query(self.model_class)
            if filters:
                for key, value in filters.items():
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.first()

    def find_by_id(self, id: int) -> object:
        with self.get_session() as session:
            return session.query(self.model_class).filter_by(id=id).first()
    def find(self, **kwargs) -> list[object]:
         with self.get_session() as session:
            query = session.query(self.model_class)
            if kwargs:
                for key, value in kwargs.items():
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.all()
    def update_by_id(self, id: int, **kwargs):
        with self.get_session() as session:
            instance = session.query(self.model_class).filter_by(id=id).first()
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                session.commit()
    
    def create(self, data: dict) -> object:
        with self.get_session() as session:
            try:
                instance = self.model_class(**data)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return instance
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error creating record: {e}")
    
    def add_all(self, data: List[dict]) -> List[object]:
        with self.get_session() as session:
            try:
                instances = [self.model_class(**item) for item in data]
                session.add_all(instances)
                session.commit()
                return instances
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"Error adding records: {e}")
    def delete(self, id: int):
        with self.get_session() as session:
            instance = session.query(self.model_class).filter_by(id=id).first()
            if instance:
                session.delete(instance)
                session.commit()
            else:
                raise Exception("Record not found")
    def commit(self):
        with self.get_session() as session:
            session.commit()

# def init_tables():
#     BaseModel.metadata.create_all(engine)
