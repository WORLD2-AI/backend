from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# database gsn
DATABASE_URL = 'mysql+pymysql://root:123456@localhost:3306/character_db'

engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class BaseModel():
    def __init__(self):
        self.session = SessionLocal()
def init_tables():
    BaseModel.metadata.create_all(engine)
