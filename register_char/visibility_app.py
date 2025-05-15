#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 获取项目根目录的绝对路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 确保项目根目录在sys.path的最前面
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from flask import Flask, jsonify, send_from_directory
from user_visibility import user_visibility_bp
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 注册蓝图
app.register_blueprint(user_visibility_bp)

@app.route('/')
def index():
    return "服务已启动", 200

@app.route('/favicon.ico')
def favicon():
    # 首先尝试从static文件夹提供favicon
    static_folder = os.path.join(app.root_path, 'static')
    if os.path.exists(os.path.join(static_folder, 'favicon.ico')):
        return send_from_directory(static_folder, 'favicon.ico')
    # 如果static文件夹中没有favicon，返回204（无内容）
    return '', 204

if __name__ == '__main__':
    logger.info("正在启动服务...")
    logger.info("服务将在 http://0.0.0.0:5000 上运行")
    logger.info("您可以通过以下地址访问：")
    logger.info("1. 本机访问: http://localhost:5000")
    logger.info("2. 局域网访问: http://192.168.1.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 