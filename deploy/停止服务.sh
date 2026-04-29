#!/bin/bash

# 停止FOF服务脚本

echo "=========================================="
echo "🛑 停止FOF服务"
echo "=========================================="

PROJECT_DIR="/root/web/fof"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"

cd $PROJECT_DIR

echo "[INFO] 停止systemd服务..."
systemctl stop fof-backend fof-frontend 2>/dev/null || true

echo "[INFO] 停止手动启动的服务..."
# 读取PID文件并停止进程
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "已停止后端进程 (PID: $BACKEND_PID)"
    fi
    rm -f logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "已停止前端进程 (PID: $FRONTEND_PID)"
    fi
    rm -f logs/frontend.pid
fi

echo "[INFO] 强制清理端口占用..."
# 使用lsof清理端口
if command -v lsof &> /dev/null; then
    BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
    
    [ -n "$BACKEND_PIDS" ] && kill -9 $BACKEND_PIDS 2>/dev/null || true
    [ -n "$FRONTEND_PIDS" ] && kill -9 $FRONTEND_PIDS 2>/dev/null || true
fi

# 使用pkill清理
pkill -f "uvicorn.*$BACKEND_PORT" 2>/dev/null || true
pkill -f "http.server.*$FRONTEND_PORT" 2>/dev/null || true

echo "[INFO] 等待进程完全停止..."
sleep 3

echo "[INFO] 检查停止结果..."
REMAINING_BACKEND=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || true)
REMAINING_FRONTEND=$(netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || true)

if [ -z "$REMAINING_BACKEND" ] && [ -z "$REMAINING_FRONTEND" ]; then
    echo "[SUCCESS] 所有服务已停止"
else
    echo "[WARNING] 仍有端口占用:"
    [ -n "$REMAINING_BACKEND" ] && echo "  后端端口: $REMAINING_BACKEND"
    [ -n "$REMAINING_FRONTEND" ] && echo "  前端端口: $REMAINING_FRONTEND"
fi

echo "=========================================="
echo "服务停止完成！"
echo "=========================================="