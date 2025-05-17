import os
import json
import urllib.parse
import logging
import traceback
import datetime
import time
import requests
import socks
import socket

# 第三方库
import redis
from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from requests_oauthlib import OAuth1Session
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user  # 移除

# 项目内部模块
from model.db import BaseModel, get_db
from model.user import User
from model.schedule import Schedule
from model.character import Character
from model.invitation_code import InvitationCode
from model.sector import Sector
from model.arena import Arena

from controllers.character_controller import character_controller
from controllers.user_controller import user_controller
from register_char.user_visibility import user_visibility_bp
from register_char.celery_task import redis_client
from utils.utils import TWITTER_API_KEY, TWITTER_API_SECRET_KEY
from config.config import REDIS_CONFIG,REDIS_PASSWORD
from tools.area_replace import replace_area

# 创建Flask应用
app = Flask(__name__)

# 应用配置
app.secret_key = "ai-hello-world:0012873"
app.permanent_session_lifetime = 3600 

# Redis配置
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host=REDIS_CONFIG.get('host',"127.0.0.1"), port=REDIS_CONFIG.get('port',6379),password=REDIS_PASSWORD, db=REDIS_CONFIG.get('db',0))
app.config['SESSION_USE_SIGNER'] = True  # 签名加密session id
app.config['SESSION_KEY_PREFIX'] = 'session:'  # redis中 key 的前缀

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

# 根路由测试
@app.route('/', methods=['GET'])
def index():
    return "server is running", 200

# 重定向到character_controller中的详情API
@app.route('/api/character/<int:character_id>/detail', methods=['GET'])
def get_character_detail_redirect(character_id):
    return redirect(f"/api/character/{character_id}/detail")

@app.route('/api/character/<int:character_id>/schedule', methods=['GET'])
def get_character_schedule_redirect(character_id):
    return redirect(f"/api/character/{character_id}/schedule")

# 添加角色详情页面路由
@app.route('/character/<int:character_id>', methods=['GET'])
def character_detail_page(character_id):
    return render_template('character_detail.html', character_id=character_id)

@app.route('/character/<int:character_id>/schedule', methods=['GET'])
def character_schedule_page(character_id):
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

# Twitter登录相关功能
@app.route('/login/twitter')
def login_twitter():
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    call_back_url = request.args.get('callback')
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
    action = request.args.get('action')

    s = User()
    if action == 'bind':
        user = s.find_by_id(session['user_id'])
        if user:
            user.twitter_id = twitter_id
            user.access_token = access_token
            user.access_token_secret = access_token_secret
            s.get_session().commit()
            return "Twitter账户绑定成功！"
    else:
        user = s.first(twitter_id=twitter_id)
        if not user:
            session['twitter_id'] = twitter_id  # 存储Twitter ID以便在注册时使用
            session['screen_name'] = screen_name  # 存储屏幕名称
            session['access_token'] = access_token
            session['access_token_secret'] = access_token_secret
            return redirect('/register')

        # 直接用 session 记录 user_id
        session['user_id'] = user.id
        if 'call_back_url' in session:
            call_back_url = session['call_back_url']
            call_back_url = urllib.parse.unquote(call_back_url)
            return redirect(call_back_url)
        else:
            return "登录成功！"

@app.route('/bind_twitter')
def bind_twitter():
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)
    request_token_url = 'https://api.twitter.com/oauth/request_token'
    fetch_response = oauth.fetch_request_token(request_token_url)
    session['request_token'] = fetch_response
    authorization_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize', action='bind')
    return redirect(authorization_url)

@app.route('/api/save_location', methods=['POST'])
def save_location():
    data = request.json
    x, y = int(data['x']), int(data['y'])
    sector_name = data['sector']
    arena_name = data['arena']
    character_id = data.get('character_id')

    # 格式化 sector 和 arena 名称
    formatted_sector_name = f"the ville:{sector_name}"
    formatted_arena_name = f"the ville:{sector_name}:{arena_name}"

    db = get_db()
    # 1. sector 唯一性
    sector = db.query(Sector).filter_by(name=formatted_sector_name).first()
    if not sector:
        sector = Sector(name=formatted_sector_name)
        db.add(sector)
        db.commit()
        db.refresh(sector)

    # 2. arena 唯一性
    arena = db.query(Arena).filter_by(name=formatted_arena_name).first()
    if arena:
        return jsonify({'error': 'arena name already exists'}), 400
    arena = Arena(name=formatted_arena_name, coordinates=f"{x},{y}")
    db.add(arena)
    db.commit()
    db.refresh(arena)

    # 3. 替换 csv 区域数字（自动 flood fill 替换）
    try:
        # replace_area('map/matrix2/maze/arena_maze.csv', x, y, arena.id)
        # replace_area('map/matrix2/maze/sector_maze.csv', x, y, sector.id)
        replace_area('map_maza/arena_maze.csv', x, y, arena.id)
        replace_area('map_maza/sector_maze.csv', x, y, sector.id)

    except Exception as e:
        return jsonify({'error': f'csv 替换失败: {str(e)}'}), 500

    # 4. character_db 表更新 sector_id
    if character_id:
        character = db.query(Character).filter_by(id=character_id).first()
        if character:
            character.sector_id = sector.id
            db.commit()

    return jsonify({'sector_id': sector.id, 'arena_id': arena.id})

@app.route('/api/test_location')
def test_location_page():
    return render_template('test_location.html')

# 添加 sector_arena_pairs API
@app.route('/api/sector_arena_pairs', methods=['GET'])
def get_sector_arena_pairs():
    try:
        db = get_db()
        arenas = db.query(Arena).all()
        result = []
        
        for arena in arenas:
            arena_data = {
                'id': arena.id,
                'name': arena.name,
                'coordinates': arena.coordinates
            }
            result.append(arena_data)
            
        return jsonify({
            'total': len(result),
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"获取arena数据失败: {str(e)}")
        return jsonify({'error': '获取数据失败'}), 500

# 添加用户资料 API
@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401
    
    try:
        user_id = session['user_id']
        db = get_db()
        user = db.query(User).filter_by(id=user_id).first()
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        profile_data = {
            'id': user.id,
            'username': user.username,
            'twitter_id': user.twitter_id,
            'screen_name': user.screen_name,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
        return jsonify(profile_data), 200
    except Exception as e:
        logger.error(f"获取用户资料失败: {str(e)}")
        return jsonify({'error': '获取用户资料失败'}), 500

if __name__ == '__main__':
    # init_tables()
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app)

    server.serve_forever()
