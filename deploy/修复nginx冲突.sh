#!/bin/bash

# 修复nginx端口冲突问题

echo "=========================================="
echo "🔧 修复nginx端口冲突"
echo "=========================================="

PROJECT_DIR="/root/web/fof"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"

cd $PROJECT_DIR

# 1. 停止nginx服务
echo "[STEP 1] 停止nginx服务..."
systemctl stop nginx 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
echo "[SUCCESS] nginx已停止"

# 2. 清理旧的uvicorn进程
echo "[STEP 2] 清理旧的uvicorn进程..."
pkill -f "uvicorn.*8505" 2>/dev/null || true
echo "[SUCCESS] 旧uvicorn进程已清理"

# 3. 创建后端.env文件
echo "[STEP 3] 创建后端.env文件..."
cat > backend/.env << EOF
# 应用配置
APP_NAME=FOF管理平台
APP_VERSION=1.0.0
DEBUG=True
SECRET_KEY=fof-secret-key-2026-change-in-production

# 数据库配置 - 使用本地SQLite
DATABASE_URL=sqlite:///./fof.db
DATABASE_ECHO=False

# JWT配置
JWT_SECRET_KEY=fof-jwt-secret-key-2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS配置
CORS_ORIGINS=["http://localhost:8507","http://47.116.187.192:8507"]

# 文件上传
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=100

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# LLM 配置（阿里云百炼 + DeepSeek）
LLM_API_KEY=sk-d9de1492e8c94256952c4d466da59bcd
LLM_MODEL=deepseek-v3.2
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_TIMEOUT=120
LLM_ENABLED=True
EOF

echo "[SUCCESS] 后端.env文件已创建"

# 4. 检查前端构建文件
echo "[STEP 4] 检查前端构建文件..."
if [ ! -d "frontend/dist" ] || [ ! "$(ls -A frontend/dist)" ]; then
    echo "[INFO] 前端构建文件不存在，开始构建..."
    cd frontend
    npm install
    NODE_ENV=production npm run build
    cd ..
    echo "[SUCCESS] 前端构建完成"
else
    echo "[SUCCESS] 前端构建文件已存在"
fi

# 5. 启动前端HTTP服务器
echo "[STEP 5] 启动前端HTTP服务器..."
cd frontend/dist
nohup python3 -m http.server $FRONTEND_PORT > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID" > ../../logs/frontend.pid
cd ../..
echo "[SUCCESS] 前端服务已启动 (PID: $FRONTEND_PID)"

# 6. 等待服务启动
echo "[STEP 6] 等待服务启动..."
sleep 5

# 7. 验证服务状态
echo "[STEP 7] 验证服务状态..."

# 检查后端
if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    echo "[SUCCESS] 后端API响应正常"
else
    echo "[ERROR] 后端API无响应"
fi

# 检查前端
if curl -s -I http://localhost:$FRONTEND_PORT/ | grep -q "200 OK"; then
    echo "[SUCCESS] 前端页面响应正常"
else
    echo "[ERROR] 前端页面无响应"
fi

# 8. 显示最终状态
echo
echo "=========================================="
echo "📊 最终状态"
echo "=========================================="

echo "端口占用情况:"
echo "端口 $BACKEND_PORT (后端):"
netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || echo "  端口未被占用"

echo "端口 $FRONTEND_PORT (前端):"
netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || echo "  端口未被占用"

echo
echo "运行进程:"
echo "Uvicorn进程:"
ps aux | grep uvicorn | grep -v grep || echo "  无Uvicorn进程"

echo "HTTP服务器进程:"
ps aux | grep "http.server" | grep -v grep || echo "  无HTTP服务器进程"

echo
echo "=========================================="
echo "🎉 修复完成！"
echo "=========================================="
echo
echo "访问地址:"
echo "  前端: http://47.116.187.192:$FRONTEND_PORT"
echo "  后端: http://47.116.187.192:$BACKEND_PORT"
echo "  API文档: http://47.116.187.192:$BACKEND_PORT/docs"
echo
echo "测试步骤:"
echo "1. 访问前端页面"
echo "2. 打开浏览器开发者工具 (F12)"
echo "3. 尝试登录: admin / admin123"
echo "4. 查看Network标签页的API请求"
echo
echo "如果仍有问题:"
echo "- 查看后端日志: tail -f logs/backend.log"
echo "- 查看前端日志: tail -f logs/frontend.log"
echo "=========================================="