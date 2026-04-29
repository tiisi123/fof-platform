#!/bin/bash

# FOF系统诊断工具 V2
# 快速诊断系统状态和常见问题

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_DIR="/root/web/fof"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"
CONDA_ENV="py310fof"
CONDA_PATH="/root/anaconda3"

# 统计
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

check_pass() {
    echo -e "  ${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_fail() {
    echo -e "  ${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

check_warn() {
    echo -e "  ${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
    ((TOTAL_CHECKS++))
}

section() {
    echo
    echo -e "${BLUE}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

echo "=========================================="
echo "🔍 FOF系统诊断工具 V2"
echo "=========================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. 基础环境检查
section "1️⃣  基础环境检查"

# 检查项目目录
if [ -d "$PROJECT_DIR" ]; then
    check_pass "项目目录存在: $PROJECT_DIR"
    cd "$PROJECT_DIR"
else
    check_fail "项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 检查conda
if [ -f "$CONDA_PATH/bin/conda" ]; then
    check_pass "Conda已安装: $CONDA_PATH"
    
    # 检查环境
    source "$CONDA_PATH/etc/profile.d/conda.sh" 2>/dev/null
    if conda env list | grep -q "$CONDA_ENV"; then
        check_pass "Conda环境存在: $CONDA_ENV"
    else
        check_fail "Conda环境不存在: $CONDA_ENV"
    fi
else
    check_fail "Conda未安装"
fi

# 检查Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js已安装: $NODE_VERSION"
else
    check_fail "Node.js未安装"
fi

# 2. 关键文件检查
section "2️⃣  关键文件检查"

# 后端文件
[ -f "backend/requirements.txt" ] && check_pass "backend/requirements.txt" || check_fail "backend/requirements.txt"
[ -f "backend/.env" ] && check_pass "backend/.env" || check_warn "backend/.env (可能需要创建)"
[ -f "backend/app/main.py" ] && check_pass "backend/app/main.py" || check_fail "backend/app/main.py"
[ -f "backend/fof.db" ] && check_pass "backend/fof.db" || check_warn "backend/fof.db (数据库文件)"

# 前端文件
[ -f "frontend/package.json" ] && check_pass "frontend/package.json" || check_fail "frontend/package.json"
[ -d "frontend/dist" ] && check_pass "frontend/dist (已构建)" || check_warn "frontend/dist (未构建)"

# systemd服务文件
[ -f "/etc/systemd/system/fof-backend.service" ] && check_pass "fof-backend.service" || check_warn "fof-backend.service (未安装)"
[ -f "/etc/systemd/system/fof-frontend.service" ] && check_pass "fof-frontend.service" || check_warn "fof-frontend.service (未安装)"

# 3. 端口和进程检查
section "3️⃣  端口和进程检查"

# 检查后端端口
BACKEND_PORT_USED=$(netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || true)
if [ -n "$BACKEND_PORT_USED" ]; then
    BACKEND_PID=$(echo "$BACKEND_PORT_USED" | awk '{print $7}' | cut -d'/' -f1)
    BACKEND_PROC=$(echo "$BACKEND_PORT_USED" | awk '{print $7}' | cut -d'/' -f2)
    check_pass "后端端口 $BACKEND_PORT 已占用 (PID: $BACKEND_PID, 进程: $BACKEND_PROC)"
else
    check_warn "后端端口 $BACKEND_PORT 未被占用"
fi

# 检查前端端口
FRONTEND_PORT_USED=$(netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || true)
if [ -n "$FRONTEND_PORT_USED" ]; then
    FRONTEND_PID=$(echo "$FRONTEND_PORT_USED" | awk '{print $7}' | cut -d'/' -f1)
    FRONTEND_PROC=$(echo "$FRONTEND_PORT_USED" | awk '{print $7}' | cut -d'/' -f2)
    check_pass "前端端口 $FRONTEND_PORT 已占用 (PID: $FRONTEND_PID, 进程: $FRONTEND_PROC)"
else
    check_warn "前端端口 $FRONTEND_PORT 未被占用"
fi

# 检查nginx冲突
NGINX_RUNNING=$(ps aux | grep nginx | grep -v grep || true)
if [ -n "$NGINX_RUNNING" ]; then
    check_warn "检测到Nginx进程（可能与前端冲突）"
fi

# 4. 服务状态检查
section "4️⃣  服务状态检查"

# 后端服务
if systemctl is-active --quiet fof-backend 2>/dev/null; then
    check_pass "后端服务运行中"
else
    check_warn "后端服务未运行"
fi

# 前端服务
if systemctl is-active --quiet fof-frontend 2>/dev/null; then
    check_pass "前端服务运行中"
else
    check_warn "前端服务未运行"
fi

# 5. API连接测试
section "5️⃣  API连接测试"

# 测试后端API
if curl -s --connect-timeout 3 http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    check_pass "后端API响应正常 (http://localhost:$BACKEND_PORT)"
else
    check_fail "后端API无响应"
fi

# 测试前端页面
if curl -s --connect-timeout 3 -I http://localhost:$FRONTEND_PORT/ 2>/dev/null | grep -q "200"; then
    check_pass "前端页面响应正常 (http://localhost:$FRONTEND_PORT)"
else
    check_fail "前端页面无响应"
fi

# 6. Python依赖检查
section "6️⃣  Python依赖检查"

if [ -f "$CONDA_PATH/bin/conda" ]; then
    source "$CONDA_PATH/etc/profile.d/conda.sh" 2>/dev/null
    conda activate "$CONDA_ENV" 2>/dev/null || true
    
    # 检查关键包
    python -c "import fastapi" 2>/dev/null && check_pass "fastapi" || check_fail "fastapi"
    python -c "import sqlalchemy" 2>/dev/null && check_pass "sqlalchemy" || check_fail "sqlalchemy"
    python -c "import pandas" 2>/dev/null && check_pass "pandas" || check_fail "pandas"
    python -c "import numpy" 2>/dev/null && check_pass "numpy" || check_fail "numpy"
    
    # 检查量化库（可选）
    python -c "import cvxpy" 2>/dev/null && check_pass "cvxpy (量化库)" || check_warn "cvxpy (量化库未安装)"
    python -c "import riskfolio" 2>/dev/null && check_pass "riskfolio-lib (量化库)" || check_warn "riskfolio-lib (量化库未安装)"
fi

# 7. 最近错误日志
section "7️⃣  最近错误日志"

# 后端日志
echo "后端服务日志 (最近10行):"
journalctl -u fof-backend -n 10 --no-pager 2>/dev/null | tail -5 || echo "  无法读取后端日志"

# 检查是否有错误
ERROR_COUNT=$(journalctl -u fof-backend -n 50 --no-pager 2>/dev/null | grep -i "error\|exception\|failed" | wc -l || echo 0)
if [ "$ERROR_COUNT" -gt 0 ]; then
    check_warn "后端日志中发现 $ERROR_COUNT 个错误"
else
    check_pass "后端日志无明显错误"
fi

# 8. 诊断总结
section "📊 诊断总结"

echo "总检查项: $TOTAL_CHECKS"
echo -e "${GREEN}通过: $PASSED_CHECKS${NC}"
echo -e "${RED}失败: $FAILED_CHECKS${NC}"
echo -e "${YELLOW}警告: $WARNINGS${NC}"

# 计算健康度
HEALTH_SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo
echo -n "系统健康度: "
if [ $HEALTH_SCORE -ge 80 ]; then
    echo -e "${GREEN}$HEALTH_SCORE% ✅ 良好${NC}"
elif [ $HEALTH_SCORE -ge 60 ]; then
    echo -e "${YELLOW}$HEALTH_SCORE% ⚠️  一般${NC}"
else
    echo -e "${RED}$HEALTH_SCORE% ❌ 需要修复${NC}"
fi

# 9. 修复建议
section "💡 修复建议"

if [ $FAILED_CHECKS -gt 0 ] || [ $WARNINGS -gt 3 ]; then
    echo "检测到问题，建议执行以下操作："
    echo
    
    # 服务未运行
    if ! systemctl is-active --quiet fof-backend 2>/dev/null; then
        echo "🔧 后端服务未运行:"
        echo "   systemctl start fof-backend"
        echo "   或: bash deploy/手动启动服务.sh"
        echo
    fi
    
    if ! systemctl is-active --quiet fof-frontend 2>/dev/null; then
        echo "🔧 前端服务未运行:"
        echo "   systemctl start fof-frontend"
        echo
    fi
    
    # API无响应
    if ! curl -s --connect-timeout 3 http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
        echo "🔧 后端API无响应，可能的原因:"
        echo "   1. 服务未启动"
        echo "   2. numpy/pandas兼容性问题: bash deploy/修复numpy冲突.sh"
        echo "   3. 端口被占用: bash deploy/彻底清理端口.sh"
        echo "   4. 查看详细日志: journalctl -u fof-backend -n 50"
        echo
    fi
    
    # 依赖缺失
    if ! python -c "import fastapi" 2>/dev/null; then
        echo "🔧 Python依赖缺失:"
        echo "   bash deploy/简化部署-v2.sh"
        echo
    fi
    
    # 量化库问题
    if ! python -c "import cvxpy" 2>/dev/null; then
        echo "💡 量化库未安装（可选）:"
        echo "   bash deploy/修复量化库安装.sh"
        echo
    fi
else
    echo -e "${GREEN}✅ 系统运行正常！${NC}"
    echo
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' || echo "your-server-ip")
    echo "访问地址:"
    echo "  前端: http://$SERVER_IP:$FRONTEND_PORT/"
    echo "  后端: http://$SERVER_IP:$BACKEND_PORT/"
    echo "  API文档: http://$SERVER_IP:$BACKEND_PORT/docs"
fi

echo
section "🛠️  常用命令"

echo "服务管理:"
echo "  systemctl status fof-backend fof-frontend"
echo "  systemctl restart fof-backend fof-frontend"
echo "  journalctl -u fof-backend -f"
echo
echo "修复工具:"
echo "  bash deploy/修复numpy冲突.sh"
echo "  bash deploy/修复量化库安装.sh"
echo "  bash deploy/彻底清理端口.sh"
echo
echo "重新部署:"
echo "  bash deploy/简化部署-v2.sh"

echo
echo "=========================================="
echo "诊断完成！"
echo "=========================================="
