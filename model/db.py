from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict
# database gsn
from config.config import DB_CONFIG
DATABASE_URL = f'mysql+pymysql://{DB_CONFIG.get("user","root")}:{DB_CONFIG.get("password","123456")}@{DB_CONFIG.get("host","127.0.0.1")}:{DB_CONFIG.get("port",3306)}/{DB_CONFIG.get("db","character_db")}'

# 创建引擎
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20
)

# 创建基础模型类
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    return db

class BaseModel():
    """基础模型类，提供通用的CRUD操作"""
    def __init__(self, **kwargs):
        self.model_class = self.get_model_class()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_model_class(self):
        """获取模型类"""
        for base in self.__class__.__mro__:
            if hasattr(base, "__tablename__"):
                return base
        raise AttributeError("未找到当前实例的模型类。")

    def get_session(self):
        """获取会话"""
        return get_db()  # 每次调用新建 Session

    def first(self, **kwargs) -> object:
        with self.get_session() as session:
            query = session.query(self.model_class)
            if kwargs:
                for key, value in kwargs.items():
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.first()

    def find_by_id(self, id: int) -> object:
        """通过ID查找记录"""
        with self.get_session() as session:
            return session.query(self.model_class).filter_by(id=id).first()
            
    def find(self, **kwargs) -> list:
        """查找符合条件的所有记录"""
        with self.get_session() as session:
            query = session.query(self.model_class)
            if kwargs:
                for key, value in kwargs.items():
                    if key == "limit":
                        query = query.limit(value)
                        continue
                    if key == "offset":
                        query = query.offset(value)
                        continue
                    if key == "order_by":
                        query = query.order_by(value)
                        continue
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.all()
            
    def update_by_id(self, id: int, **kwargs):
        """通过ID更新记录"""
        with self.get_session() as session:
            instance = session.query(self.model_class).filter_by(id=id).first()
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                session.commit()
    
    def create(self, data: dict) -> object:
        """创建记录"""
        with self.get_session() as session:
            try:
                instance = self.model_class(**data)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return instance
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"创建记录失败: {e}")
    
    def add_all(self, data: List[dict]) -> List[object]:
        """批量添加记录"""
        with self.get_session() as session:
            try:
                instances = [self.model_class(**item) for item in data]
                session.add_all(instances)
                session.commit()
                return instances
            except SQLAlchemyError as e:
                session.rollback()
                raise Exception(f"批量添加记录失败: {e}")

    def find_all(self) -> list:
        """获取所有记录"""
        with self.get_session() as session:
            query = session.query(self.model_class)
            return query.all()
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