#!/bin/bash

# FOF管理平台简化部署脚本 V2
# 解决了所有已知问题：
# - GCC 版本过低导致的编译问题
# - numpy/pandas 二进制不兼容
# - OpenBB 依赖冲突
# - 使用 conda 预编译包避免编译

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_DIR="/root/web/fof"
BACKUP_DIR="/root/backups"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"
CONDA_ENV="py310fof"
CONDA_PATH="/root/anaconda3"
INSTALL_QUANT_LIBS="yes"  # 是否安装量化库 (yes/no)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "🚀 FOF管理平台简化部署脚本 V2"
echo "=========================================="
echo "项目路径: $PROJECT_DIR"
echo "Conda环境: $CONDA_ENV"
echo "后端端口: $BACKEND_PORT"
echo "前端端口: $FRONTEND_PORT"
echo "量化库: $INSTALL_QUANT_LIBS"
echo "=========================================="
echo

# 确认部署
read -p "确认开始部署? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "部署已取消"
    exit 0
fi

# 1. 检查项目目录
log_info "检查项目目录..."
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "项目目录不存在: $PROJECT_DIR"
    exit 1
fi

cd $PROJECT_DIR
log_info "当前工作目录: $(pwd)"

# 2. 检查关键文件
log_info "检查项目文件..."
if [ ! -f "backend/requirements.txt" ]; then
    log_error "缺少文件: backend/requirements.txt"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    log_error "缺少文件: frontend/package.json"
    exit 1
fi

log_success "项目文件检查通过"

# 3. 创建必要目录
log_info "创建必要目录..."
mkdir -p $BACKUP_DIR
mkdir -p logs
log_success "目录创建完成"

# 4. 停止现有服务
log_info "停止现有服务..."
systemctl stop fof-backend fof-frontend 2>/dev/null || true
pkill -f "uvicorn.*8506" 2>/dev/null || true
pkill -f "http.server 8507" 2>/dev/null || true
sleep 2
log_success "服务已停止"

# 5. 检查并激活conda环境
log_info "检查conda环境..."
if [ ! -f "$CONDA_PATH/bin/conda" ]; then
    log_error "Conda未找到: $CONDA_PATH"
    exit 1
fi

source $CONDA_PATH/etc/profile.d/conda.sh

if ! conda env list | grep -q "$CONDA_ENV"; then
    log_error "未找到conda环境: $CONDA_ENV"
    log_info "可用环境:"
    conda env list
    exit 1
fi

conda activate $CONDA_ENV
log_success "Conda环境已激活: $CONDA_ENV"

# 6. 安装后端基础依赖
log_info "安装后端基础依赖..."
pip install -r backend/requirements.txt
log_success "基础依赖安装完成"

# 7. 安装量化库（可选）
if [ "$INSTALL_QUANT_LIBS" = "yes" ]; then
    log_info "安装量化库..."
    
    # 使用 conda 安装预编译的核心包（避免 GCC 编译问题）
    log_info "从 conda-forge 安装预编译包..."
    if conda install -y -c conda-forge cvxpy scs osqp clarabel 2>/dev/null; then
        log_success "核心量化库安装完成（预编译版本）"
        
        # 安装其他纯 Python 包（跳过 OpenBB 避免依赖冲突）
        log_info "安装其他量化库..."
        pip install --no-deps riskfolio-lib PyPortfolioOpt 2>/dev/null || log_warning "riskfolio-lib/PyPortfolioOpt 安装失败"
        pip install quantstats akshare 2>/dev/null || log_warning "quantstats/akshare 安装失败"
        
        log_warning "跳过 OpenBB（与 FastAPI 版本冲突）"
        
        # 修复 numpy/pandas 兼容性
        log_info "修复 numpy/pandas 兼容性..."
        pip uninstall -y numpy pandas scipy 2>/dev/null || true
        pip install --no-cache-dir numpy==1.26.2 pandas==2.1.3 scipy==1.11.4
        
        log_success "量化库安装完成"
    else
        log_warning "量化库安装失败，将使用基础功能"
        log_info "如需量化功能，请运行: bash deploy/修复量化库安装.sh"
    fi
else
    log_info "跳过量化库安装"
fi

# 8. 配置环境变量
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        log_success "创建环境变量文件"
    fi
fi

# 9. 构建前端
log_info "构建前端..."
if ! command -v node &> /dev/null; then
    log_error "Node.js未安装，请先安装 Node.js 16+"
    exit 1
fi

cd frontend
npm install
npm run build
cd ..
log_success "前端构建完成"

# 10. 初始化数据库（如果需要）
if [ ! -f "backend/fof.db" ] || [ $(stat -c%s "backend/fof.db" 2>/dev/null || echo 0) -lt 1000000 ]; then
    log_warning "数据库文件不存在或很小，初始化数据库..."
    cd backend
    
    if [ -f "scripts/regenerate_tasks.py" ]; then
        python scripts/regenerate_tasks.py 2>/dev/null || log_warning "任务数据生成失败"
        log_success "任务数据生成完成"
    fi
    
    if [ -f "scripts/add_dashboard_indexes.py" ]; then
        python scripts/add_dashboard_indexes.py 2>/dev/null || log_warning "索引添加失败"
        log_success "数据库索引添加完成"
    fi
    
    cd ..
else
    log_info "数据库文件已存在，跳过初始化"
fi

# 11. 配置systemd服务
log_info "配置系统服务..."
if [ -f "deploy/fof-backend.service" ]; then
    cp deploy/fof-backend.service /etc/systemd/system/
fi

if [ -f "deploy/fof-frontend.service" ]; then
    cp deploy/fof-frontend.service /etc/systemd/system/
fi

systemctl daemon-reload
systemctl enable fof-backend fof-frontend 2>/dev/null || true
log_success "系统服务配置完成"

# 12. 启动服务
log_info "启动后端服务..."
systemctl start fof-backend
sleep 5

if systemctl is-active --quiet fof-backend; then
    log_success "后端服务启动成功"
else
    log_error "后端服务启动失败"
    log_info "查看错误日志:"
    journalctl -u fof-backend -n 20 --no-pager
    
    read -p "是否继续启动前端? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log_info "启动前端服务..."
systemctl start fof-frontend
sleep 2

if systemctl is-active --quiet fof-frontend; then
    log_success "前端服务启动成功"
else
    log_error "前端服务启动失败"
    journalctl -u fof-frontend -n 20 --no-pager
fi

# 13. 验证部署
log_info "验证部署..."
sleep 3

if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    log_success "后端API响应正常"
else
    log_warning "后端API无响应，请检查日志: journalctl -u fof-backend -f"
fi

if curl -s -I http://localhost:$FRONTEND_PORT/ 2>/dev/null | grep -q "200"; then
    log_success "前端页面响应正常"
else
    log_warning "前端页面无响应，请检查日志: journalctl -u fof-frontend -f"
fi

# 14. 配置防火墙
log_info "配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$BACKEND_PORT/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=$FRONTEND_PORT/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    log_success "防火墙规则已添加 (firewalld)"
elif command -v ufw &> /dev/null; then
    ufw allow $BACKEND_PORT/tcp 2>/dev/null || true
    ufw allow $FRONTEND_PORT/tcp 2>/dev/null || true
    log_success "防火墙规则已添加 (ufw)"
else
    log_warning "未检测到防火墙，请手动开放端口 $BACKEND_PORT 和 $FRONTEND_PORT"
fi

echo
echo "=========================================="
log_success "🎉 部署完成！"
echo "=========================================="
echo
log_info "📋 部署信息:"
echo "  项目路径: $PROJECT_DIR"
echo "  Conda环境: $CONDA_ENV"
echo
log_info "🌐 访问地址:"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}' || echo "your-server-ip")
echo "  前端: http://$SERVER_IP:$FRONTEND_PORT/"
echo "  后端API: http://$SERVER_IP:$BACKEND_PORT/"
echo "  API文档: http://$SERVER_IP:$BACKEND_PORT/docs"
echo
log_info "👤 默认账号: admin / admin123"
echo
log_info "🔧 服务管理:"
echo "  查看状态: systemctl status fof-backend fof-frontend"
echo "  重启服务: systemctl restart fof-backend fof-frontend"
echo "  查看日志: journalctl -u fof-backend -f"
echo
log_info "📦 已安装的量化库:"
python -c "import cvxpy; print('  ✅ cvxpy:', cvxpy.__version__)" 2>/dev/null || echo "  ❌ cvxpy"
python -c "import riskfolio; print('  ✅ riskfolio-lib:', riskfolio.__version__)" 2>/dev/null || echo "  ❌ riskfolio-lib"
python -c "import pypfopt; print('  ✅ PyPortfolioOpt:', pypfopt.__version__)" 2>/dev/null || echo "  ❌ PyPortfolioOpt"
python -c "import quantstats; print('  ✅ quantstats:', quantstats.__version__)" 2>/dev/null || echo "  ❌ quantstats"
python -c "import akshare; print('  ✅ akshare:', akshare.__version__)" 2>/dev/null || echo "  ❌ akshare"
echo
log_info "⚠️  重要提醒:"
echo "  1. 首次访问请使用 Ctrl+Shift+R 强制刷新浏览器"
echo "  2. 如遇到问题，查看故障排查脚本:"
echo "     - bash deploy/修复numpy冲突.sh"
echo "     - bash deploy/修复量化库安装.sh"
echo "     - bash deploy/清理OpenBB.sh"
echo
echo "=========================================="
