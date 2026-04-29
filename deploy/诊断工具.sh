#!/bin/bash

# FOF系统诊断工具

echo "=========================================="
echo "🔍 FOF系统诊断工具"
echo "=========================================="

PROJECT_DIR="/root/web/fof"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"
SERVER_IP="47.116.187.192"

cd $PROJECT_DIR

echo "[INFO] 项目目录: $(pwd)"
echo "[INFO] 服务器IP: $SERVER_IP"
echo "[INFO] 后端端口: $BACKEND_PORT"
echo "[INFO] 前端端口: $FRONTEND_PORT"

echo
echo "=========================================="
echo "📋 系统状态检查"
echo "=========================================="

# 1. 检查端口占用
echo "[1] 端口占用情况:"
echo "后端端口 $BACKEND_PORT:"
netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || echo "  端口未被占用"

echo "前端端口 $FRONTEND_PORT:"
netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || echo "  端口未被占用"

# 2. 检查进程状态
echo
echo "[2] 相关进程:"
echo "Uvicorn进程:"
ps aux | grep uvicorn | grep -v grep || echo "  无Uvicorn进程"

echo "HTTP服务器进程:"
ps aux | grep "http.server" | grep -v grep || echo "  无HTTP服务器进程"

echo "Nginx进程:"
ps aux | grep nginx | grep -v grep || echo "  无Nginx进程"

# 3. 检查systemd服务
echo
echo "[3] Systemd服务状态:"
echo "后端服务:"
systemctl is-active fof-backend 2>/dev/null || echo "  服务未运行"

echo "前端服务:"
systemctl is-active fof-frontend 2>/dev/null || echo "  服务未运行"

# 4. 检查文件存在性
echo
echo "[4] 关键文件检查:"
echo "后端配置:"
[ -f "backend/.env" ] && echo "  ✅ backend/.env 存在" || echo "  ❌ backend/.env 不存在"
[ -f "backend/app/main.py" ] && echo "  ✅ backend/app/main.py 存在" || echo "  ❌ backend/app/main.py 不存在"

echo "前端构建:"
[ -d "frontend/dist" ] && echo "  ✅ frontend/dist 存在" || echo "  ❌ frontend/dist 不存在"
[ -f "frontend/.env.production" ] && echo "  ✅ frontend/.env.production 存在" || echo "  ❌ frontend/.env.production 不存在"

# 5. 测试API连接
echo
echo "=========================================="
echo "🌐 网络连接测试"
echo "=========================================="

echo "[5] API连接测试:"
echo "测试后端健康检查:"
if curl -s --connect-timeout 5 http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    echo "  ✅ 后端API响应正常"
    curl -s http://localhost:$BACKEND_PORT/api/v1/health | head -1
else
    echo "  ❌ 后端API无响应"
fi

echo "测试前端页面:"
if curl -s --connect-timeout 5 -I http://localhost:$FRONTEND_PORT/ | grep -q "200 OK"; then
    echo "  ✅ 前端页面响应正常"
else
    echo "  ❌ 前端页面无响应"
fi

# 6. 检查配置一致性
echo
echo "=========================================="
echo "⚙️ 配置一致性检查"
echo "=========================================="

echo "[6] 端口配置检查:"
echo "前端API地址配置:"
if [ -f "frontend/.env.production" ]; then
    grep VITE_API_BASE_URL frontend/.env.production
else
    echo "  ❌ 前端生产环境配置不存在"
fi

echo "后端CORS配置:"
if [ -f "backend/app/core/config.py" ]; then
    grep -A 3 "CORS_ORIGINS" backend/app/core/config.py | head -4
else
    echo "  ❌ 后端配置文件不存在"
fi

# 7. 日志检查
echo
echo "=========================================="
echo "📝 日志检查"
echo "=========================================="

echo "[7] 最近日志:"
if [ -f "logs/backend.log" ]; then
    echo "后端日志 (最后5行):"
    tail -5 logs/backend.log 2>/dev/null || echo "  无法读取后端日志"
else
    echo "  ❌ 后端日志文件不存在"
fi

if [ -f "logs/frontend.log" ]; then
    echo "前端日志 (最后5行):"
    tail -5 logs/frontend.log 2>/dev/null || echo "  无法读取前端日志"
else
    echo "  ❌ 前端日志文件不存在"
fi

echo
echo "=========================================="
echo "💡 诊断建议"
echo "=========================================="

# 根据检查结果给出建议
BACKEND_RUNNING=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || true)
FRONTEND_RUNNING=$(netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || true)

if [ -z "$BACKEND_RUNNING" ]; then
    echo "🔧 后端未运行，建议:"
    echo "   bash deploy/手动启动服务.sh"
fi

if [ -z "$FRONTEND_RUNNING" ]; then
    echo "🔧 前端未运行，建议:"
    echo "   bash deploy/修复nginx冲突.sh"
fi

if [ -n "$BACKEND_RUNNING" ] && [ -n "$FRONTEND_RUNNING" ]; then
    echo "✅ 服务运行正常！"
    echo "   访问地址: http://$SERVER_IP:$FRONTEND_PORT"
fi

echo
echo "🛠️ 常用修复命令:"
echo "   停止所有服务: bash deploy/停止服务.sh"
echo "   清理端口占用: bash deploy/彻底清理端口.sh"
echo "   修复nginx冲突: bash deploy/修复nginx冲突.sh"
echo "   完整重新部署: bash deploy/一键部署.sh"

echo
echo "=========================================="
echo "诊断完成！"
echo "=========================================="