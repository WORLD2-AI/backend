from flask import redirect, session, request, jsonify
from requests_oauthlib import OAuth1Session
from reverie.backend_server.login.db_oprate import *

# Twitter API credentials
TWITTER_API_KEY = 'ySnmcu2uwwnHacFOmlvd8IuJR'
TWITTER_API_SECRET_KEY = 'kGZyR9H40a9lroCsSSvBlKeCqRYCjBi7gplXsoHdSpSnjMtl0X'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    twitter_id = db.Column(db.String(50), unique=True, nullable=False)
    access_token = db.Column(db.String(200), nullable=False)
    access_token_secret = db.Column(db.String(200), nullable=False)
    screen_name = db.Column(db.String(200), nullable=False)


@app.route('/')
def home():
    return '欢迎使用 Twitter 登录！<br><a href="/login">登录 Twitter</a>'


@app.route('/login')
def login():
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

    # 获取用户信息
    twitter_id = response.get('user_id')
    access_token = response.get('oauth_token')
    access_token_secret = response.get('oauth_token_secret')
    screen_name = response.get('screen_name')

    # 检查用户是否已存在
    user = User.query.filter_by(twitter_id=twitter_id).first()
    if not user:
        # 新用户，保存到数据库
        user = User(twitter_id=twitter_id, access_token=access_token, access_token_secret=access_token_secret,
                    screen_name=screen_name)
        db.session.add(user)
        db.session.commit()

    session['user_id'] = twitter_id
    return f"登录成功！用户 ID：{twitter_id}"


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/')

    user = User.query.filter_by(twitter_id=session['user_id']).first()
    return jsonify({
        'twitter_id': user.twitter_id,
        'access_token': user.access_token
    })


if __name__ == '__main__':
    app.run(debug=True)
