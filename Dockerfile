# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置标签信息
LABEL maintainer="Xianyu Auto Reply System"
LABEL version="1.0.0"
LABEL description="闲鱼自动回复系统 - Docker版本"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        tzdata \
        curl \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        fonts-dejavu-core \
        && apt-get clean \
        && rm -rf /var/lib/apt/lists/*

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/data /app/backups && \
    chmod 777 /app/logs /app/data /app/backups

# 注意: 为了简化权限问题，使用root用户运行
# 在生产环境中，建议配置适当的用户映射

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 创建启动脚本
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'set -e' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo 'echo "🚀 启动闲鱼自动回复系统..."' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 数据库将在应用启动时自动初始化' >> /app/entrypoint.sh && \
    echo 'echo "📊 数据库将在应用启动时自动初始化..."' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo '# 启动主应用' >> /app/entrypoint.sh && \
    echo 'echo "🎯 启动主应用..."' >> /app/entrypoint.sh && \
    echo 'exec python Start.py' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# 启动命令
CMD ["/app/entrypoint.sh"]