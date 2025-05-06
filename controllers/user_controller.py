from flask import Blueprint, request, jsonify, session, redirect
from flask import request, jsonify, render_template
from model.user import User
from model.invitation_code import InvitationCode
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import logout_user, login_required
user_controller = Blueprint('user', __name__)

@user_controller.route('/api/register_user', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        invitation_code = request.form['invitation_code']
        
        # 验证表单数据
        if not username or not password or not invitation_code:
            return render_template('login/register.html', error="用户名、密码和邀请码不能为空")
        
        # 检查用户是否已存在
        user_model = User()
        existing_user = user_model.first(username=username)
        if existing_user:
            return render_template('login/register.html', error="用户名已存在")

        # 验证邀请码
        inv_code_model = InvitationCode()
        if not inv_code_model.verify_code(invitation_code):
            return render_template('login/register.html', error="邀请码无效或已被使用")

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
            return render_template('login/register_success.html', username=username)
        
        except Exception as e:
            return render_template('login/register.html', error=f"注册失败: {str(e)}")

    # GET 请求，显示注册表单
    return render_template('login/register.html')


@user_controller.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 验证表单数据
        if not username or not password:
            return render_template('login/login.html', error="用户名和密码不能为空")

        user = User().first({"username": username})
        if user and check_password_hash(user.password_hash, password):
            # 登录成功，设置session
            session['user_id'] = user.id
            
            # 检查是否有回调URL
            if 'call_back_url' in session:
                call_back_url = session.pop('call_back_url')
                return redirect(call_back_url)
                
            # 否则返回登录成功消息
            return redirect('/')
        else:
            # 登录失败
            return render_template('login/login.html', error="用户名或密码错误")

    # GET 请求，显示登录表单
    return render_template('login/login.html')

@user_controller.route('/user/info')
def get_user_info():
# 判断session中的user_id是否存在
    if 'user_id' in session:
        user = User().find_by_id(session['user_id'])
        if user:
            return jsonify({
                'data': user.to_dict() if hasattr(user, 'to_dict') else {
                    'id': user.id,
                    'username': user.username
                }
            })
    # 返回401状态
    return jsonify({
        'data': None
    }), 401


@user_controller.route('/api/user/profile')
def profile():
    """
    查询账号
    """
    if 'user_id' not in session:
        return redirect('/')

    user = User().find_by_id(session['user_id'])
    return jsonify({
        "status":"success",
        'id': user.id,
        'username': user.username,
        'twitter_id': user.twitter_id,
        # 'access_token': user.access_token
    })


@user_controller.route('/logout', methods=['POST'])
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

        #终止Flask-Login会话
        # logout_user()

        return jsonify({
            "status": "success",
            "message": "logout success!"
        }), 200

        # # 方式二：重定向到登录页
        # response = redirect(url_for('login'))
        # response.delete_cookie('session')  # 清除客户端cookie
        # return response

    except Exception as e:
        print(f"退出异常: {str(e)}")
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
        codes = invitation_code.find()
        
        return jsonify({
            "status": "success",
            "data": [code.to_dict() for code in codes]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取邀请码失败: {str(e)}"
        }), 500
