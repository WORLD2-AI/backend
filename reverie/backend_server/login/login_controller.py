from flask import redirect, session, request, jsonify, render_template
from requests_oauthlib import OAuth1Session
from werkzeug.security import check_password_hash, generate_password_hash

from reverie.backend_server.login.db_oprate import *

# Twitter API credentials
TWITTER_API_KEY = 'ySnmcu2uwwnHacFOmlvd8IuJR'
TWITTER_API_SECRET_KEY = 'kGZyR9H40a9lroCsSSvBlKeCqRYCjBi7gplXsoHdSpSnjMtl0X'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    twitter_id = db.Column(db.String(50), unique=True, nullable=False)
    access_token = db.Column(db.String(200), nullable=False)
    access_token_secret = db.Column(db.String(200), nullable=False)
    screen_name = db.Column(db.String(200), nullable=False)


@app.route('/')
def home():
    return '欢迎使用HelloWorld！<br><a href="/login">登录 Twitter</a><br><a href="/register">注册</a>'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return '用户名已存在', 400

        hashed_password = generate_password_hash(password)

        # 获取 Twitter ID 和屏幕名称
        twitter_id = session.pop('twitter_id', None)
        screen_name = session.pop('screen_name', None)
        access_token = session.pop('access_token', None)
        access_token_secret = session.pop('access_token_secret', None)

        new_user = User(username=username, password_hash=hashed_password, twitter_id=twitter_id,
                        screen_name=screen_name, access_token=access_token, access_token_secret=access_token_secret)

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id  # 登录用户
        return f"注册成功！用户 ID：{new_user.id}"

    return render_template('login/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return '登录成功！'
        return '用户名或密码错误', 401

    return render_template('login/login.html')


@app.route('/login/twitter')
def login_twitter():
    oauth = OAuth1Session(TWITTER_API_KEY, client_secret=TWITTER_API_SECRET_KEY)
    request_token_url = 'https://api.twitter.com/oauth/request_token'

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

    if action == 'bind':
        # 绑定 Twitter 账户
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            user.twitter_id = twitter_id
            user.access_token = access_token
            user.access_token_secret = access_token_secret
            db.session.commit()
            return "Twitter 账户绑定成功！"
    else:
        # 登录逻辑
        # 检查用户是否已注册
        user = User.query.filter_by(twitter_id=twitter_id).first()
        if not user:
            # 用户未注册，重定向到注册页面
            session['twitter_id'] = twitter_id  # 存储 Twitter ID 以便在注册时使用
            session['screen_name'] = screen_name  # 存储屏幕名称
            session['access_token'] = access_token
            session['access_token_secret'] = access_token_secret
            return redirect('/register')

        session['user_id'] = user.id
        return f"登录成功！用户 ID：{user.id}"


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


@app.route('/profile')
def profile():
    """
    查询账号
    """
    if 'user_id' not in session:
        return redirect('/')

    user = User.query.get(session['user_id'])
    return jsonify({
        'username': user.username,
        'twitter_id': user.twitter_id,
        'access_token': user.access_token
    })


if __name__ == '__main__':
    app.run(debug=True)
