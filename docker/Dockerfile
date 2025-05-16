# 使用官方 Python 3.9.12 镜像作为基础
FROM python:3.9.10-slim

# 设置工作目录
WORKDIR /app

# 可选：设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖（如果有需要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    procps \
    libpq-dev \
    supervisor \
    && rm -rf /var/lib/apt/lists/*
# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN /usr/local/bin/python -m pip install --upgrade pip -i  https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install --no-cache-dir -r requirements.txt -i  https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 复制项目文件到容器中
COPY . .
RUN rm -f /app/config/config.py
COPY config/config_release.py /app/config/config.py
COPY ./supervisor/supervisord.conf /etc/supervisor/conf.d/
EXPOSE 5000
EXPOSE 8000
RUN mkdir -p /var/log/supervisor
WORKDIR /app
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]