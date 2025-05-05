from flask import Blueprint, request, jsonify, session,redirect
from flask import request, jsonify, render_template
from model.user import User
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import logout_user, login_required
user_controller = Blueprint('user', __name__)

@user_controller.route('/api/register_user', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        s = User().get_session()
        if s.query(User).filter_by(username=username).first():
            return 'user exists', 400

        hashed_password = generate_password_hash(password)

        # 获取 Twitter ID 和屏幕名称
        twitter_id = session.pop('twitter_id', None)
        screen_name = session.pop('screen_name', None)
        access_token = session.pop('access_token', None)
        access_token_secret = session.pop('access_token_secret', None)

        new_user = User(username=username, password_hash=hashed_password, twitter_id=twitter_id,
                        screen_name=screen_name, access_token=access_token, access_token_secret=access_token_secret)
        
        
        s.add(new_user)
        s.commit()

        session['user_id'] = new_user.id  # 登录用户
        return f"register success ID：{new_user.id}"

    return render_template('login/register.html')


@user_controller.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User().first({"username":username})
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return 'login success'
        return 'login failed', 401

    return render_template('login/login.html')
@user_controller.route('/user/info')
def get_user_info():
# 判断session中的user_id是否存在
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            return jsonify({
                'data': user
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
@login_required
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
        logout_user()

        return jsonify({
            "status": "success",
            "message": "logout success!"
        }), 200

        # # 方式二：重定向到登录页
        # response = redirect(url_for('login'))
        # response.delete_cookie('session')  # 清除客户端cookie
        # return response

    except Exception as e:
        app.logger.error(f"退出异常: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "退出失败，请重试"
        }), 500
