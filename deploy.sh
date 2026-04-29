#!/bin/bash
set -e

echo "========================================="
echo "  FOF管理平台 一键部署脚本"
echo "========================================="

PROJECT_DIR="/root/web/fof"
REPO_URL="https://gitee.com/ts_tiisi/fof_v2.git"
CONDA_ENV="py310fof"

# ========== 1. 拉取代码 ==========
echo ""
echo "[1/5] 拉取代码..."
if [ -d "$PROJECT_DIR" ]; then
    echo "目录已存在，拉取最新代码..."
    cd "$PROJECT_DIR" && git pull origin master
else
    mkdir -p /root/web
    git clone "$REPO_URL" "$PROJECT_DIR"
fi

# ========== 2. 后端部署 ==========
echo ""
echo "[2/5] 部署后端..."
cd "$PROJECT_DIR/backend"

# 激活 conda 环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $CONDA_ENV
echo "当前 Python: $(which python) ($(python --version))"

# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件
if [ ! -f ".env" ]; then
cat > .env << 'EOF'
APP_NAME=FOF管理平台
APP_VERSION=1.0.0
DEBUG=False
SECRET_KEY=fof-production-secret-key-change-me
DATABASE_URL=sqlite:///../fof.db
JWT_SECRET_KEY=fof-jwt-secret-key-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
EOF
echo ".env 文件已创建"
fi

mkdir -p logs uploads

# ========== 3. 前端部署 ==========
echo ""
echo "[3/5] 部署前端..."
cd "$PROJECT_DIR/frontend"

if ! command -v node &> /dev/null || [ "$(node -v | grep -oP '\d+' | head -1)" -lt 16 ]; then
    echo "安装 Node.js 18..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash - 2>/dev/null || \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - 2>/dev/null
    yum install -y nodejs 2>/dev/null || apt-get install -y nodejs 2>/dev/null
fi
echo "Node: $(node --version), npm: $(npm --version)"

npm install
npm run build
echo "前端构建完成"

# ========== 4. Nginx 配置 ==========
echo ""
echo "[4/5] 配置 Nginx..."

cat > /etc/nginx/conf.d/fof.conf << 'EOF'
server {
    listen 8507;
    server_name _;

    root /root/web/fof/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8506;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
        client_max_body_size 100m;
    }
}
EOF

nginx -t && systemctl restart nginx && systemctl enable nginx
echo "Nginx 已配置 (端口 8507)"

# ========== 5. 启动后端服务 ==========
echo ""
echo "[5/5] 启动后端服务..."

CONDA_BASE=$(conda info --base)
UVICORN_PATH="$CONDA_BASE/envs/$CONDA_ENV/bin/uvicorn"

cat > /etc/systemd/system/fof-backend.service << EOF
[Unit]
Description=FOF Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/web/fof/backend
ExecStart=$UVICORN_PATH app.main:app --host 0.0.0.0 --port 8506
Restart=always
RestartSec=5
Environment="PATH=$CONDA_BASE/envs/$CONDA_ENV/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart fof-backend
systemctl enable fof-backend

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "  访问地址: http://47.116.187.192:8507"
echo "  API文档:  http://47.116.187.192:8506/api/docs"
echo ""
echo "  常用命令:"
echo "    查看日志:  journalctl -u fof-backend -f"
echo "    重启后端:  systemctl restart fof-backend"
echo "    重启Nginx: systemctl restart nginx"
echo ""
