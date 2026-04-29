#!/bin/bash

# 手动启动服务（不重新构建前端）

echo "=========================================="
echo "🚀 手动启动FOF服务"
echo "=========================================="

PROJECT_DIR="/root/web/fof"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"
CONDA_ENV="py310fof"
CONDA_PATH="/root/anaconda3"

cd $PROJECT_DIR

# 1. 强制停止现有服务和进程
echo "[INFO] 强制停止现有服务..."
systemctl stop fof-backend fof-frontend 2>/dev/null || true

# 使用lsof查找并杀死占用端口的进程
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)

if [ -n "$BACKEND_PIDS" ]; then
    echo "[INFO] 杀死占用后端端口的进程: $BACKEND_PIDS"
    kill -9 $BACKEND_PIDS 2>/dev/null || true
fi

if [ -n "$FRONTEND_PIDS" ]; then
    echo "[INFO] 杀死占用前端端口的进程: $FRONTEND_PIDS"
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
fi

# 使用pkill清理
pkill -f "uvicorn.*$BACKEND_PORT" 2>/dev/null || true
pkill -f "python3.*http.server.*$FRONTEND_PORT" 2>/dev/null || true
pkill -f "http.server $FRONTEND_PORT" 2>/dev/null || true

echo "[INFO] 等待进程完全停止..."
sleep 5

# 最终检查
REMAINING_BACKEND=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
REMAINING_FRONTEND=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)

if [ -n "$REMAINING_BACKEND" ] || [ -n "$REMAINING_FRONTEND" ]; then
    echo "[ERROR] 端口仍被占用，请运行: bash deploy/强制清理端口.sh"
    exit 1
fi

echo "[SUCCESS] 所有端口已释放"

# 2. 启动后端服务
echo "[INFO] 启动后端服务..."
cd backend

# 激活conda环境
source $CONDA_PATH/etc/profile.d/conda.sh
conda activate $CONDA_ENV

# 启动后端
nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > ../logs/backend-manual.log 2>&1 &
BACKEND_PID=$!

cd ..

echo "[INFO] 后端服务已启动 (PID: $BACKEND_PID)"
echo "后端PID: $BACKEND_PID" > logs/backend.pid

# 等待后端启动
sleep 5

# 3. 测试后端
if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    echo "[SUCCESS] 后端API响应正常"
else
    echo "[ERROR] 后端API无响应，检查日志: tail -f logs/backend-manual.log"
fi

# 4. 启动前端服务
echo "[INFO] 启动前端服务..."

# 检查前端构建文件
if [ ! -d "frontend/dist" ] || [ ! "$(ls -A frontend/dist)" ]; then
    echo "[ERROR] 前端构建文件不存在，需要先构建前端"
    echo "请运行: bash deploy/修复服务问题.sh"
    exit 1
fi

cd frontend/dist
nohup python3 -m http.server $FRONTEND_PORT > ../../logs/frontend-manual.log 2>&1 &
FRONTEND_PID=$!
cd ../..

echo "[INFO] 前端服务已启动 (PID: $FRONTEND_PID)"
echo "前端PID: $FRONTEND_PID" > logs/frontend.pid

# 等待前端启动
sleep 3

# 5. 测试前端
if curl -s -I http://localhost:$FRONTEND_PORT/ | grep -q "200 OK"; then
    echo "[SUCCESS] 前端页面响应正常"
else
    echo "[ERROR] 前端页面无响应，检查日志: tail -f logs/frontend-manual.log"
fi

# 6. 显示状态
echo
echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo
echo "服务信息:"
echo "  后端PID: $BACKEND_PID (端口: $BACKEND_PORT)"
echo "  前端PID: $FRONTEND_PID (端口: $FRONTEND_PORT)"
echo
echo "访问地址:"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo "  前端: http://$SERVER_IP:$FRONTEND_PORT"
echo "  后端: http://$SERVER_IP:$BACKEND_PORT"
echo "  API文档: http://$SERVER_IP:$BACKEND_PORT/docs"
echo
echo "日志文件:"
echo "  后端日志: tail -f logs/backend-manual.log"
echo "  前端日志: tail -f logs/frontend-manual.log"
echo
echo "停止服务:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  或运行: bash deploy/停止手动服务.sh"
echo "=========================================="