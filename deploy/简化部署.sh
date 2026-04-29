#!/bin/bash

# FOF管理平台简化部署脚本
# 适用于已克隆的项目，无需Git操作

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
echo "🚀 FOF管理平台简化部署脚本"
echo "=========================================="
echo "项目路径: $PROJECT_DIR"
echo "Conda环境: $CONDA_ENV"
echo "后端端口: $BACKEND_PORT"
echo "前端端口: $FRONTEND_PORT"
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
MISSING_FILES=()

if [ ! -f "backend/requirements.txt" ]; then
    MISSING_FILES+=("backend/requirements.txt")
fi

if [ ! -f "frontend/package.json" ]; then
    MISSING_FILES+=("frontend/package.json")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    log_error "项目文件不完整，缺失:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
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
log_success "服务已停止"

# 5. 检查conda环境
log_info "检查conda环境..."
if [ ! -f "$CONDA_PATH/bin/conda" ]; then
    log_error "Conda未找到，请确认路径: $CONDA_PATH"
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
log_success "Conda环境检查通过"

# 6. 安装后端依赖
log_info "安装后端依赖..."
pip install -r backend/requirements.txt

# Optional quant dependencies should not block base deployment.
if [ -f "backend/requirements-open-source.txt" ]; then
    log_info "Try installing optional quant dependencies (non-blocking)..."
    if pip install -r backend/requirements-open-source.txt; then
        log_success "Optional quant dependencies installed"
    else
        log_warning "Optional quant dependencies failed; continue with native fallback engine"
    fi
filog_success "后端依赖安装完成"

# 7. 配置环境变量
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        log_success "创建环境变量文件"
    fi
fi

# 8. 安装前端依赖
log_info "安装前端依赖..."
if ! command -v node &> /dev/null; then
    log_error "Node.js未安装，请先安装Node.js 16+"
    exit 1
fi

cd frontend
npm install
npm run build
cd ..
log_success "前端构建完成"

# 9. 初始化数据库（如果需要）
if [ ! -f "backend/fof.db" ] || [ $(stat -c%s "backend/fof.db" 2>/dev/null || echo 0) -lt 1000000 ]; then
    log_warning "数据库文件不存在或很小，初始化数据库..."
    cd backend
    conda activate $CONDA_ENV
    
    if [ -f "scripts/init_empty_database.py" ]; then
        python scripts/init_empty_database.py
        log_success "数据库初始化完成"
    fi
    
    if [ -f "scripts/regenerate_tasks.py" ]; then
        python scripts/regenerate_tasks.py
        log_success "任务数据生成完成"
    fi
    
    cd ..
else
    log_info "数据库文件已存在，跳过初始化"
fi

# 10. 配置systemd服务
log_info "配置系统服务..."
cp deploy/fof-backend.service /etc/systemd/system/
cp deploy/fof-frontend.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable fof-backend fof-frontend
log_success "系统服务配置完成"

# 11. 启动服务
log_info "启动服务..."
systemctl start fof-backend
sleep 3

if systemctl is-active --quiet fof-backend; then
    log_success "后端服务启动成功"
else
    log_error "后端服务启动失败"
    journalctl -u fof-backend -n 10
fi

systemctl start fof-frontend
sleep 2

if systemctl is-active --quiet fof-frontend; then
    log_success "前端服务启动成功"
else
    log_error "前端服务启动失败"
    journalctl -u fof-frontend -n 10
fi

# 12. 验证部署
log_info "验证部署..."
sleep 5

if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
    log_success "后端API响应正常"
else
    log_warning "后端API无响应，请检查日志"
fi

if curl -s -I http://localhost:$FRONTEND_PORT/ | grep -q "200 OK"; then
    log_success "前端页面响应正常"
else
    log_warning "前端页面无响应，请检查日志"
fi

# 13. 配置防火墙
log_info "配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow $BACKEND_PORT/tcp
    ufw allow $FRONTEND_PORT/tcp
    log_success "防火墙规则已添加 (ufw)"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$BACKEND_PORT/tcp
    firewall-cmd --permanent --add-port=$FRONTEND_PORT/tcp
    firewall-cmd --reload
    log_success "防火墙规则已添加 (firewalld)"
else
    log_warning "未检测到防火墙，请手动开放端口 $BACKEND_PORT 和 $FRONTEND_PORT"
fi

echo
echo "=========================================="
log_success "🎉 部署完成！"
echo "=========================================="
echo
log_info "访问地址:"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo "  前端: http://$SERVER_IP:$FRONTEND_PORT/"
echo "  后端: http://$SERVER_IP:$BACKEND_PORT/"
echo "  API文档: http://$SERVER_IP:$BACKEND_PORT/docs"
echo
log_info "默认账号: admin / admin123"
echo
log_info "服务管理:"
echo "  查看状态: systemctl status fof-backend fof-frontend"
echo "  重启服务: systemctl restart fof-backend fof-frontend"
echo "  查看日志: journalctl -u fof-backend -f"
echo
if [ ! -f "backend/fof.db" ] || [ $(stat -c%s "backend/fof.db" 2>/dev/null || echo 0) -lt 10000000 ]; then
    log_warning "⚠️  建议上传完整的数据库文件到 backend/fof.db"
fi
echo "=========================================="