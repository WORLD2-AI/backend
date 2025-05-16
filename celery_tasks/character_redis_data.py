from model.character import Character
from model.schedule import Schedule
class CharacterRedisData(Character):
    position = [0, 0]
    action = ""
    start_minute = 0
    duration = 0
    emoji = ""
    path = []
    site= ""
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_id':self.user_id,
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
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            "position": self.position if self.position else [0, 0],
            "start_minute":self.start_minute,
            "duration":self.duration,
            "action":self.action,
            "emoji":self.emoji,
            "path" : self.path,
            "site":self.site,
        }
        

