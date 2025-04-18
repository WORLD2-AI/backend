from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# MySQL数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/character_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 角色状态常量
CHARACTER_STATUS = {
    'PENDING': '待创建',
    'PROCESSING': '处理中',
    'COMPLETED': '创建完成',
    'FAILED': '创建失败'
}

# 数据库模型
class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    innate = db.Column(db.Text, nullable=False)
    learned = db.Column(db.Text, nullable=False)
    currently = db.Column(db.Text, nullable=False)
    lifestyle = db.Column(db.String(255), nullable=False)
    wake_time = db.Column(db.Integer, default=7)  # 起床时间（小时）
    sleep_time = db.Column(db.Integer, default=22)  # 睡觉时间（小时）
    status = db.Column(db.String(20), default=CHARACTER_STATUS['PENDING'], nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # 关联日程表
    schedules = db.relationship('Schedule', backref='character', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'sex': self.sex,
            'innate': self.innate,
            'learned': self.learned,
            'currently': self.currently,
            'lifestyle': self.lifestyle,
            'wake_time': self.wake_time,
            'sleep_time': self.sleep_time,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

# 日程表模型
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    time = db.Column(db.String(20), nullable=False)  # 时间点
    action = db.Column(db.String(100), nullable=False)  # 活动内容
    location = db.Column(db.String(100), nullable=False)  # 活动地点
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'time': self.time,
            'action': self.action,
            'location': self.location,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

# 创建数据库表
with app.app_context():
    db.create_all() 