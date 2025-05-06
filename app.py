from flask import request, jsonify, render_template
import base
from flask import redirect, session, request, jsonify, render_template
from requests_oauthlib import OAuth1Session
from model.user import User
import urllib.parse


from controllers.character_controller import character_controller
from controllers.user_controller import user_controller
from model.schedule import  Schedule
from model.character import Character  # 导入角色模型
from model.invitation_code import InvitationCode  # 导入邀请码模型

from common.redis_client import redis_handler
import json
import redis
import logging
import traceback
from flask_cors import CORS
from flask import Flask
# from model.db import BaseModel, init_tables  # 导入初始化函数
from register_char.user_visibility import user_visibility_bp
from utils.utils import *
# 创建Flask应用
import os
import datetime  # 导入 datetime 模块用于处理时间

app = Flask(__name__)
app.secret_key = "ai-hello-world:0012873"
app.permanent_session_lifetime = 3600 
CORS(app)


app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, password='000000')
app.config['SESSION_USE_SIGNER'] = True  # 签名加密session id
app.config['SESSION_KEY_PREFIX'] = 'session:'  # redis中 key 的前缀
# MySQL数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/character_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(character_controller)
app.register_blueprint(user_controller)
app.register_blueprint(user_visibility_bp)
# 配置CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# # 确保数据库表存在 - 使用兼容的初始化方式
# def setup_database():
#     """初始化数据库表"""
#     init_tables()
#     logger.info("数据库表初始化完成")

# # 在应用启动时初始化数据库
# with app.app_context():
#     setup_database()

# 根路由测试
@app.route('/', methods=['GET'])
def index():
    return "server is running", 200

# 添加获取角色详情的API路由
@app.route('/api/character/<int:character_id>/detail', methods=['GET'])
def get_character_detail(character_id):
    """
    根据角色ID获取角色详情，包括角色名字、当前时间的活动、活动地点和地点图标路径
    """
    try:
        # 获取当前时间（分钟数）
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        # 获取角色的日程安排
        schedule = Schedule()
        schedules = schedule.find(user_id=character_id)
        
        if not schedules:
            return jsonify({"error": "未找到该角色的日程安排"}), 404
        
        # 找出当前时间正在进行的活动
        current_activity = None
        for s in schedules:
            start_minute = s.start_minute
            end_minute = start_minute + s.duration
            
            # 检查当前时间是否在活动时间范围内
            if start_minute <= current_minutes < end_minute:
                current_activity = s
                break
        
        # 如果没有找到当前活动，返回第一个活动
        if not current_activity and schedules:
            current_activity = schedules[0]
        
        # 从日程安排中获取角色名字
        character_name = current_activity.name if current_activity else "未知角色"
        
        result = {
            "id": character_id,
            "name": character_name
        }
        
        # 如果找到了活动，添加活动相关信息
        if current_activity:
            # 解析地点信息 - 从site字段中提取第一个冒号后第二个冒号前的文字
            site_info = current_activity.site
            location = ""
            if ":" in site_info:
                parts = site_info.split(":")
                if len(parts) > 1:
                    location = parts[1].strip()
                    # 如果有第二个冒号，截取到第二个冒号前
                    if ":" in location:
                        location = location.split(":")[0].strip()
            
            # 构建地点图标路径 - 完整路径，指向根目录下的icon文件夹
            icon_path = f"/icon/{location}.png" if location else ""
            
            result.update({
                "activity": current_activity.action,
                "location": location,
                "icon_path": icon_path,
                "icon_file": f"{location}.png",  # 添加图标文件名
                "icon_dir": "icon",  # 添加图标目录
                "start_minute": current_activity.start_minute,
                "duration": current_activity.duration,
                "current_time_minutes": current_minutes
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"获取角色详情失败: {str(e)}"}), 500

# 添加角色详情页面路由
@app.route('/character/<int:character_id>', methods=['GET'])
def character_detail_page(character_id):
    """
    角色详情页面，展示角色的信息和当前活动
    """
    return render_template('character_detail.html', character_id=character_id)

# 添加用户注册路由
@app.route('/register')
def register_page():
    return redirect('/api/register_user')

# 添加角色注册路由
@app.route('/register_role')
def register_role_page():
    return redirect('/api/register_role')

# 添加角色列表路由
@app.route('/character_list')
def character_list_redirect():
    return redirect('/characters')

@app.route('/login/twitter')
def login_twitter():
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    call_back_url = request.args.get('callback')
    # 将call_bakc_url 添加到session中
    session['call_back_url'] = call_back_url
    try:
        response = oauth.fetch_request_token(request_token_url)
    except Exception as e:
        return f"请求令牌失败: {str(e)}", 500

    session['request_token'] = response
    authorization_url = oauth.authorization_url('https://api.twitter.com/oauth/authenticate')
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    request_token = session.pop('request_token', None)
    oauth_verifier = request.args.get('oauth_verifier')

    if not request_token or not oauth_verifier:
        return '缺少请求令牌或验证器', 400

    oauth = OAuth1Session(TWITTER_API_KEY,
                          client_secret=TWITTER_API_SECRET_KEY,
                          resource_owner_key=request_token['oauth_token'],
                          resource_owner_secret=request_token['oauth_token_secret'],
                          verifier=oauth_verifier)

    access_token_url = 'https://api.twitter.com/oauth/access_token'

    try:
        response = oauth.fetch_access_token(access_token_url)
    except Exception as e:
        return f"获取访问令牌失败: {str(e)}", 500

    twitter_id = response.get('user_id')
    access_token = response.get('oauth_token')
    access_token_secret = response.get('oauth_token_secret')
    screen_name = response.get('screen_name')
    # 判断是登录还是绑定
    action = request.args.get('action')

    s = User()
    if action == 'bind':
        # 绑定 Twitter 账户
        user = s.find_by_id(session['user_id'])
        if user:
            user.twitter_id = twitter_id
            user.access_token = access_token
            user.access_token_secret = access_token_secret
            s.get_session().commit()
            return "Twitter 账户绑定成功！"
    else:
        # 登录逻辑
        # 检查用户是否已注册
        user = s.first(twitter_id=twitter_id)
        if not user:
            # 用户未注册，重定向到注册页面
            session['twitter_id'] = twitter_id  # 存储 Twitter ID 以便在注册时使用
            session['screen_name'] = screen_name  # 存储屏幕名称
            session['access_token'] = access_token
            session['access_token_secret'] = access_token_secret
            return redirect('/register')

        session['user_id'] = user.id
        # 如果session中有call_back_url，则重定向到call_back_url
        if 'call_back_url' in session:
            call_back_url = session['call_back_url']
            call_back_url = urllib.parse.unquote(call_back_url)
            return redirect(call_back_url)
        else:
            return "登录成功！"


@app.route('/bind_twitter')
def bind_twitter():
    """
    对已经注册过账号，单独进行绑定推特
    """
    # 创建 OAuth 认证会话
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)

    # 获取请求令牌
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = oauth.fetch_request_token(request_token_url)

    # 将请求令牌存入会话
    session['request_token'] = fetch_response

    # 重定向用户到 Twitter 授权页面 带上绑定参数
    authorization_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize', action='bind')
    return redirect(authorization_url)

if __name__ == '__main__':
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)