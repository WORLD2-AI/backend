from sqlalchemy import  Column, Integer, String
from model.db import BaseModel,Base

class Schedule(BaseModel,Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    start_minute = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    action = Column(String(500), nullable=False)
    site = Column(String(500), nullable=False)
    emoji = Column(String(20), nullable=False)
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'start_minute': self.start_minute,
            'duration': self.duration,
            'action': self.action,
            'site': self.site,
            'emoji': self.emoji
        }

    # def create_table(self):
    #     """create action schedule table"""
    #     try:            
    #         self.session.execute("""
    #             CREATE TABLE IF NOT EXISTS schedule (
    #             id INT AUTO_INCREMENT PRIMARY KEY,
    #             user_id INT NOT NULL COMMENT '用户ID',
    #             name VARCHAR(255) NOT NULL COMMENT 'user name',
    #             start_minute INT NOT NULL COMMENT 'action start minute',
    #             duration INT NOT NULL COMMENT 'minutes',
    #             action VARCHAR(255) NOT NULL COMMENT 'action description',
    #             site VARCHAR(255) COMMENT 'position of action',
    #             emoji VARCHAR(10) COMMENT 'emoji'
    #             )
    #         """)
    #         print("create tables success")
    #     except pymysql.Error as e:
    #         print(f"create table failed,err: {e}")
    #         raise