from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict
# database gsn
DATABASE_URL = 'mysql+pymysql://root:root@localhost:3306/character_db'

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class BaseModel():
    def __init__(self):
        self.session = None 
        self.model_class = self.get_model_class()
        # self.session = SessionLocal()
    def get_model_class(self):
        """
        动态获取当前实例所属的子类的模型类。
        """
        for base in self.__class__.__mro__:
            if hasattr(base, "__tablename__"):  # 查找模型类
                return base
        raise AttributeError("Model class not found for the current instance.")
    def find_by_id(self,id: int)-> object:
        return self.get_session().query(self.model_class).filter_by(id=id).first()
    def update_by_id(self, id: int, **kwargs):
        instance = self.find_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.get_session().commit()
    def get_all(self, filters: Optional[Dict] = None) -> List[object]:
        """
        获取所有记录，支持传入过滤条件
        """
        query = self.get_session().query(self.model_class)
        if filters:
            for key, value in filters.items():
                query = query.filter(getattr(self.model_class, key) == value)
        return query.all()
    def create(self, data: dict) -> object:
        """
        创建一条新记录
        """
        try:
            instance = self.model_class(**data)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Error creating record: {e}")
    def add_all(self, data: List[dict]) -> List[object]:
        """
        批量添加记录
        """
        try:
            instances = [self.model_class(**item) for item in data]
            self.get_session().add_all(instances)
            self.get_session().commit()
            return instances
        except SQLAlchemyError as e:
            self.get_session().rollback()
            raise Exception(f"Error adding records: {e}")
    def get_session(self):
        if self.session is None:
            self.session = SessionLocal()
        return self.session

def init_tables():
    BaseModel.metadata.create_all(engine)
