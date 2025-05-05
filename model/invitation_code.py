from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from model.db import BaseModel, Base
import random
import string

class InvitationCode(BaseModel, Base):
    __tablename__ = 'invitation_codes'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(16), unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(Integer, nullable=True)  # 使用该邀请码的用户ID
    created_at = Column(DateTime, default=func.now())
    used_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'is_used': self.is_used,
            'used_by': self.used_by,
            'created_at': self.created_at,
            'used_at': self.used_at
        }
    
    @staticmethod
    def generate_code(length=8):
        """生成随机邀请码"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def generate_batch(count=100):
        """批量生成指定数量的邀请码"""
        codes = []
        for _ in range(count):
            code = InvitationCode.generate_code()
            codes.append({'code': code})
        return codes
    
    def verify_code(self, code):
        """验证邀请码是否有效"""
        with self.get_session() as session:
            invitation = session.query(InvitationCode).filter_by(code=code, is_used=False).first()
            return invitation is not None
    
    def use_code(self, code, user_id):
        """使用邀请码"""
        from datetime import datetime
        with self.get_session() as session:
            invitation = session.query(InvitationCode).filter_by(code=code, is_used=False).first()
            if invitation:
                invitation.is_used = True
                invitation.used_by = user_id
                invitation.used_at = datetime.now()
                session.commit()
                return True
            return False 