#!/bin/bash

# 彻底清理端口占用问题

echo "=========================================="
echo "💀 彻底清理端口占用"
echo "=========================================="

BACKEND_PORT="8506"
FRONTEND_PORT="8507"

echo "[INFO] 开始彻底清理端口 $BACKEND_PORT 和 $FRONTEND_PORT..."

# 1. 停止所有systemd服务
echo "[STEP 1] 停止systemd服务..."
systemctl stop fof-backend fof-frontend 2>/dev/null || true
systemctl disable fof-backend fof-frontend 2>/dev/null || true

# 2. 使用多种方法查找并杀死进程
echo "[STEP 2] 查找并杀死占用端口的进程..."

# 方法1: 使用lsof
if command -v lsof &> /dev/null; then
    echo "使用lsof查找进程..."
    BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
    FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
    
    if [ -n "$BACKEND_PIDS" ]; then
        echo "杀死后端进程: $BACKEND_PIDS"
        kill -9 $BACKEND_PIDS 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PIDS" ]; then
        echo "杀死前端进程: $FRONTEND_PIDS"
        kill -9 $FRONTEND_PIDS 2>/dev/null || true
    fi
fi

# 方法2: 使用netstat + awk
echo "使用netstat查找进程..."
BACKEND_PIDS=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-' || true)
FRONTEND_PIDS=$(netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " | awk '{print $7}' | cut -d'/' -f1 | grep -v '-' || true)

if [ -n "$BACKEND_PIDS" ]; then
    echo "netstat找到后端进程: $BACKEND_PIDS"
    kill -9 $BACKEND_PIDS 2>/dev/null || true
fi

if [ -n "$FRONTEND_PIDS" ]; then
    echo "netstat找到前端进程: $FRONTEND_PIDS"
    kill -9 $FRONTEND_PIDS 2>/dev/null || true
fi

# 方法3: 使用ss命令
if command -v ss &> /dev/null; then
    echo "使用ss查找进程..."
    BACKEND_PIDS=$(ss -tlnp 2>/dev/null | grep ":$BACKEND_PORT " | grep -o 'pid=[0-9]*' | cut -d'=' -f2 || true)
    FRONTEND_PIDS=$(ss -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " | grep -o 'pid=[0-9]*' | cut -d'=' -f2 || true)
    
    if [ -n "$BACKEND_PIDS" ]; then
        echo "ss找到后端进程: $BACKEND_PIDS"
        kill -9 $BACKEND_PIDS 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PIDS" ]; then
        echo "ss找到前端进程: $FRONTEND_PIDS"
        kill -9 $FRONTEND_PIDS 2>/dev/null || true
    fi
fi

# 3. 使用pkill强制清理
echo "[STEP 3] 使用pkill强制清理..."
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "http.server" 2>/dev/null || true
pkill -9 -f "python3.*8506" 2>/dev/null || true
pkill -9 -f "python3.*8507" 2>/dev/null || true
pkill -9 -f ":8506" 2>/dev/null || true
pkill -9 -f ":8507" 2>/dev/null || true

# 4. 清理可能的nohup进程
echo "[STEP 4] 清理nohup进程..."
pkill -9 -f "nohup.*uvicorn" 2>/dev/null || true
pkill -9 -f "nohup.*http.server" 2>/dev/null || true

# 5. 清理Python进程
echo "[STEP 5] 清理Python进程..."
ps aux | grep -E "(uvicorn|http\.server)" | grep -E "($BACKEND_PORT|$FRONTEND_PORT)" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true

# 6. 等待进程完全停止
echo "[STEP 6] 等待进程完全停止..."
sleep 10

# 7. 最终检查
echo "[STEP 7] 最终检查端口状态..."
echo "端口 $BACKEND_PORT 状态:"
netstat -tlnp | grep ":$BACKEND_PORT " || echo "  端口已释放"

echo "端口 $FRONTEND_PORT 状态:"
netstat -tlnp | grep ":$FRONTEND_PORT " || echo "  端口已释放"

# 8. 如果还有占用，使用fuser强制清理
if command -v fuser &> /dev/null; then
    echo "[STEP 8] 使用fuser最后清理..."
    fuser -k $BACKEND_PORT/tcp 2>/dev/null || true
    fuser -k $FRONTEND_PORT/tcp 2>/dev/null || true
    sleep 2
fi

# 9. 清理PID文件
echo "[STEP 9] 清理PID文件..."
rm -f /root/web/fof/logs/backend.pid
rm -f /root/web/fof/logs/frontend.pid

# 10. 最终验证
echo "[STEP 10] 最终验证..."
FINAL_BACKEND=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || true)
FINAL_FRONTEND=$(netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || true)

if [ -z "$FINAL_BACKEND" ] && [ -z "$FINAL_FRONTEND" ]; then
    echo "[SUCCESS] 所有端口已彻底清理"
else
    echo "[WARNING] 仍有端口占用:"
    [ -n "$FINAL_BACKEND" ] && echo "  后端端口: $FINAL_BACKEND"
    [ -n "$FINAL_FRONTEND" ] && echo "  前端端口: $FINAL_FRONTEND"
    
    echo "[INFO] 尝试重启网络服务..."
    systemctl restart networking 2>/dev/null || true
    systemctl restart network 2>/dev/null || true
fi

echo
echo "=========================================="
echo "端口清理完成！"
echo "=========================================="
echo
echo "现在可以安全启动服务:"
echo "bash deploy/手动启动服务.sh"
echo "=========================================="