import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='../../../environment/frontend_server/templates')
app.secret_key = os.urandom(24)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:HelloWorld#2025@45.32.140.156:3366/ai_hello_world'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
