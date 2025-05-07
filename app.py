import os
import json
import urllib.parse
import logging
import traceback
import datetime

# 第三方库
import redis
from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from requests_oauthlib import OAuth1Session

# 项目内部模块
from model.db import BaseModel, init_tables
from model.user import User
from model.schdule import Schedule
from model.character import Character
from model.invitation_code import InvitationCode

from controllers.character_controller import character_controller
from controllers.user_controller import user_controller
from register_char.user_visibility import user_visibility_bp
from register_char.celery_task import redis_client
from utils.utils import TWITTER_API_KEY, TWITTER_API_SECRET_KEY
from config.config import REDIS_CONFIG
# 创建Flask应用
app = Flask(__name__)

# 应用配置
app.secret_key = "ai-hello-world:0012873"
app.permanent_session_lifetime = 3600 

# Redis配置
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host=REDIS_CONFIG.get('host',"127.0.0.1"), port=REDIS_CONFIG.get('port',6379), db=0, password=REDIS_CONFIG.get('password',""))
app.config['SESSION_USE_SIGNER'] = True  # 签名加密session id
app.config['SESSION_KEY_PREFIX'] = 'session:'  # redis中 key 的前缀

# MySQL数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/character_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

# 注册蓝图
app.register_blueprint(character_controller)
app.register_blueprint(user_controller)
app.register_blueprint(user_visibility_bp)

# 确保数据库表存在
def setup_database():
    """初始化数据库表"""
    init_tables()
    logger.info("数据库表初始化完成")

# 根路由测试
@app.route('/', methods=['GET'])
def index():
    return "server is running", 200

# 重定向到character_controller中的详情API
@app.route('/api/character/<int:character_id>/detail', methods=['GET'])
def get_character_detail_redirect(character_id):
    """重定向到character_controller中的角色详情API"""
    return redirect(f"/api/character/{character_id}/detail")

@app.route('/api/character/<int:character_id>/schedule', methods=['GET'])
def get_character_schedule_redirect(character_id):
    """重定向到character_controller中的角色日程安排API"""
    return redirect(f"/api/character/{character_id}/schedule")

# 添加角色详情页面路由
@app.route('/character/<int:character_id>', methods=['GET'])
def character_detail_page(character_id):
    """角色详情页面，展示角色的信息和当前活动"""
    return render_template('character_detail.html', character_id=character_id)

@app.route('/character/<int:character_id>/schedule', methods=['GET'])
def character_schedule_page(character_id):
    """角色日程安排页面，展示角色的所有日程安排"""
    return render_template('character_schedule.html', character_id=character_id)

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

# Twitter登录相关功能，后续应该移到专门的蓝图中
@app.route('/login/twitter')
def login_twitter():
    """处理Twitter登录请求"""
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    call_back_url = request.args.get('callback')
    # 将callback_url添加到session中
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
    """处理Twitter授权回调"""
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
        # 绑定Twitter账户
        user = s.find_by_id(session['user_id'])
        if user:
            user.twitter_id = twitter_id
            user.access_token = access_token
            user.access_token_secret = access_token_secret
            s.get_session().commit()
            return "Twitter账户绑定成功！"
    else:
        # 登录逻辑
        # 检查用户是否已注册
        user = s.first(twitter_id=twitter_id)
        if not user:
            # 用户未注册，重定向到注册页面
            session['twitter_id'] = twitter_id  # 存储Twitter ID以便在注册时使用
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
    """对已经注册过账号，单独进行绑定推特"""
    # 创建OAuth认证会话
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)

    # 获取请求令牌
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = oauth.fetch_request_token(request_token_url)

    # 将请求令牌存入会话
    session['request_token'] = fetch_response

    # 重定向用户到Twitter授权页面带上绑定参数
    authorization_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize', action='bind')
    return redirect(authorization_url)

if __name__ == '__main__':
    # 在应用启动时初始化数据库
    with app.app_context():
        setup_database()
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)