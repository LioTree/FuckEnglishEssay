FROM python:3.9-slim

# 安装系统依赖（icdiff用于差异比较，aha用于HTML转换）
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    && pip3 install icdiff \
    && apt-get install -y aha \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["flask", "run"]
