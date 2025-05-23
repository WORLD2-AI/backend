from flask import Blueprint, request, jsonify, session, redirect, render_template
from model.user import User
from model.invitation_code import InvitationCode
from werkzeug.security import check_password_hash, generate_password_hash
# from flask_login import login_user, logout_user, login_required, current_user  # 移除
from flask import Blueprint, request, jsonify, session, redirect
from flask import request, jsonify, render_template
from model.user import User
from model.invitation_code import InvitationCode
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import logout_user, login_required
from common.redis_client import redis_handler
user_controller = Blueprint('user', __name__)

@user_controller.route('/api/register_user', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        invitation_code = request.form['invitation_code']
        
        # 验证表单数据
        if not username or not password or not invitation_code:
            return  jsonify({'success': False, 'message': 'username or password or invitation code could not be null'}), 500
        
        # 检查用户是否已存在
        user_model = User()
        existing_user = user_model.first(username=username)
        if existing_user:
            return  jsonify({'success': False, 'message': 'register faild, username exists'}), 500

        # 验证邀请码
        inv_code_model = InvitationCode()
        if not inv_code_model.verify_code(invitation_code):
            return  jsonify({'success': False, 'message': 'register faild, inviled invitation code'}), 500

        try:
            # 密码加密
            hashed_password = generate_password_hash(password)

            # 获取 Twitter ID 和屏幕名称
            twitter_id = session.pop('twitter_id', None)
            screen_name = session.pop('screen_name', None)
            access_token = session.pop('access_token', None)
            access_token_secret = session.pop('access_token_secret', None)

            # 创建新用户
            new_user = User(
                username=username, 
                password_hash=hashed_password, 
                twitter_id=twitter_id,
                screen_name=screen_name, 
                access_token=access_token, 
                access_token_secret=access_token_secret
            )
            
            s = user_model.get_session()
            s.add(new_user)
            s.commit()

            # 标记邀请码已使用
            inv_code_model.use_code(invitation_code, new_user.id)

            # 登录用户
            session['user_id'] = new_user.id
            
            # 检查是否有回调URL
            if 'call_back_url' in session:
                call_back_url = session.pop('call_back_url')
                return redirect(call_back_url)
            
            # 否则返回注册成功页面
            return  jsonify({'success': True, 'message': 'register success'}), 200
        
        except Exception as e:
            return jsonify({'success': False, 'message': e}), 500

    # GET 请求，显示注册表单
    # return render_template('login/register.html')


@user_controller.route('/api/login', methods=['POST'])
def login():
    # if request.method == 'GET':
    #     return render_template('login/login.html')
        
    # POST 请求处理登录逻辑
    # 支持 application/json 和 form-data 两种方式
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    # 验证表单数据
    if not username or not password:
        return jsonify({'success': False, 'message': 'user name or password  should not be null'}), 400

    user = User().first(username=username)
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({'success': True, 'message': 'login success'}), 200
    else:
        return jsonify({'success': False, 'message': 'user name or password is incorrect'}), 401

@user_controller.route('/user/info')
def get_user_info():
    user_id = session.get('user_id')
    if user_id:
        user = User().find_by_id(user_id)
        if user:
            user_dict = user.to_dict() if hasattr(user, 'to_dict') else {
                'id': user.id,
                'user_id': user.id,
                'username': user.username
            }
            user_dict['user_id'] = user.id
            return jsonify({
                'data': user_dict
            })
    # 返回401状态
    return jsonify({
        'data': None
    }), 401


def login_required_view(func):
    # 用于替代 flask_login 的 login_required 装饰器
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': '未登录'}), 401
        return func(*args, **kwargs)
    return wrapper

@user_controller.route('/api/user/profile')
@login_required_view
def profile():
    """
    查询账号
    """
    user_id = session.get('user_id')
    user = User().find_by_id(user_id)
    return jsonify({
        "status":"success",
        'id': user.id,
        'user_id': user.id,
        'username': user.username,
        'twitter_id': user.twitter_id,
        # 'access_token': user.access_token
    })


@user_controller.route('/logout', methods=['POST'])
@login_required_view
def logout():
    """
    安全退出登录
    """
    try:
        # 清除会话中的关键数据
        session_keys_to_remove = [
            'user_id',  # 用户ID
            'twitter_id',  # Twitter ID
            'access_token',  # 访问令牌（正确键名）
            'access_token_secret',  # 访问令牌密钥（正确键名）
            'call_back_url'  # 回调URL
        ]

        # 安全删除会话键值
        for key in session_keys_to_remove:
            session.pop(key, None)  # 使用安全删除方式

        # 清除所有会话数据
        session.clear()

        return jsonify({
            "status": "success",
            "message": "logout success!"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "退出失败，请重试"
        }), 500

# 添加邀请码生成接口（仅限管理员使用）
@user_controller.route('/api/admin/generate_invitation_codes', methods=['POST'])
def generate_invitation_codes():
    # 这里应该添加管理员权限验证
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    # 简单示例：用户ID为1的是管理员（实际应用中应该有更完善的权限系统）
    if session['user_id'] != 1:
        return jsonify({"status": "error", "message": "权限不足"}), 403
    
    try:
        count = request.json.get('count', 100)
        invitation_code = InvitationCode()
        codes = InvitationCode.generate_batch(count)
        invitation_code.add_all(codes)
        
        return jsonify({
            "status": "success",
            "message": f"成功生成{count}个邀请码"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"生成邀请码失败: {str(e)}"
        }), 500

# 查看可用邀请码（仅限管理员）
@user_controller.route('/api/admin/invitation_codes', methods=['GET'])
def list_invitation_codes():
    # 权限验证
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "未授权访问"}), 401
    
    if session['user_id'] != 1:
        return jsonify({"status": "error", "message": "权限不足"}), 403
    
    try:
        invitation_code = InvitationCode()
        codes = invitation_code.find_all()
        
        return jsonify({
            "status": "success",
            "data": [code.to_dict() for code in codes]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取邀请码失败: {str(e)}"
        }), 500
