# 1. 使用官方 Python 轻量版镜像
FROM python:3.10-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 设置环境变量：防止 Python 产生 .pyc 文件，并确保日志实时输出
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. 安装系统依赖（如果你的 MySQL 驱动需要编译，可能需要额外包）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev \
    libmagic1\
    && rm -rf /var/lib/apt/lists/*

# 5. 先复制 requirements 并安装，利用 Docker 缓存机制加速后续构建
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 复制项目所有代码到容器
COPY . .

# 7. 暴露 FastAPI 默认端口
EXPOSE 8080

# 8. 启动命令（配合 uvicorn，注意这里的 host 必须是 0.0.0.0）
# Zeabur 建议使用 8080 端口，或者在后台自行配置
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8080"]