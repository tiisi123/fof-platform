#!/bin/bash

# FOF管理平台一键部署脚本
# Git仓库: https://gitee.com/ts_tiisi/fof_v2.git
# Conda环境: py310fof

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_DIR="/root/web/fof"
BACKUP_DIR="/root/backups"
BACKEND_PORT="8506"
FRONTEND_PORT="8507"
GIT_REPO="https://gitee.com/ts_tiisi/fof_v2.git"
CONDA_ENV="py310fof"
CONDA_PATH="/root/anaconda3"
INSTALL_QUANT_LIBS="yes"  # 是否安装量化库 (yes/no)

# 日志函数
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查conda环境
check_conda() {
    log_info "检查conda环境..."
    
    if [ ! -f "$CONDA_PATH/bin/conda" ]; then
        log_error "Conda未找到，请确认路径: $CONDA_PATH"
        exit 1
    fi
    
    source $CONDA_PATH/etc/profile.d/conda.sh
    
    if ! conda env list | grep -q "$CONDA_ENV"; then
        log_error "Conda环境 '$CONDA_ENV' 不存在"
        log_info "可用环境列表:"
        conda env list
        exit 1
    fi
    
    log_success "Conda环境检查通过"
}

# 安装系统依赖
install_system_dependencies() {
    if [ "$INSTALL_QUANT_LIBS" != "yes" ]; then
        log_info "跳过系统依赖安装（量化库已禁用）"
        return 0
    fi
    
    log_info "安装系统依赖（用于量化库编译）..."
    
    # 检测系统类型
    if [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        log_info "检测到 CentOS/RHEL 系统"
        
        # 安装开发工具和BLAS库
        yum groupinstall -y "Development Tools" || log_warning "开发工具可能已安装"
        yum install -y openblas-devel lapack-devel cmake || {
            log_error "系统依赖安装失败"
            log_info "请手动运行: yum install -y openblas-devel lapack-devel cmake"
            exit 1
        }
        
    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        log_info "检测到 Debian/Ubuntu 系统"
        
        apt-get update
        apt-get install -y build-essential libopenblas-dev liblapack-dev cmake || {
            log_error "系统依赖安装失败"
            log_info "请手动运行: apt-get install -y build-essential libopenblas-dev liblapack-dev cmake"
            exit 1
        }
        
    else
        log_warning "未识别的系统类型，请手动安装以下依赖:"
        echo "  - gcc/g++ 编译器"
        echo "  - OpenBLAS 开发库"
        echo "  - LAPACK 开发库"
        echo "  - CMake"
        read -p "是否已手动安装这些依赖? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "请先安装系统依赖"
            exit 1
        fi
    fi
    
    log_success "系统依赖安装完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    mkdir -p $PROJECT_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $PROJECT_DIR/logs
    log_success "目录创建完成"
}

# 备份现有项目
backup_existing() {
    if [ -d "$PROJECT_DIR" ] && [ "$(ls -A $PROJECT_DIR 2>/dev/null)" ]; then
        log_info "备份现有项目..."
        BACKUP_NAME="fof-backup-$(date +%Y%m%d_%H%M%S)"
        cp -r $PROJECT_DIR $BACKUP_DIR/$BACKUP_NAME
        log_success "备份完成: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."
    
    # 停止systemd服务
    systemctl stop fof-backend 2>/dev/null || true
    systemctl stop fof-frontend 2>/dev/null || true
    
    # 停止进程
    pkill -f "uvicorn.*app.main:app.*--port $BACKEND_PORT" 2>/dev/null || true
    pkill -f "python3.*http.server $FRONTEND_PORT" 2>/dev/null || true
    
    sleep 2
    log_success "服务已停止"
}

# 更新代码
update_code() {
    log_info "更新代码..."
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        log_info "请先手动克隆项目: git clone $GIT_REPO $PROJECT_DIR"
        exit 1
    fi
    
    cd $PROJECT_DIR
    
    if [ -d ".git" ]; then
        git pull origin master
        log_success "代码更新完成"
    else
        log_warning "不是Git仓库，跳过代码更新"
    fi
    
    # 显示版本信息
    if [ -d ".git" ]; then
        log_info "当前版本:"
        git log --oneline -3
    fi
}

# 设置后端环境
setup_backend() {
    log_info "设置后端环境..."
    
    # 确保在项目根目录
    cd $PROJECT_DIR
    log_info "当前工作目录: $(pwd)"
    
    # 检查关键文件
    if [ ! -f "backend/requirements.txt" ]; then
        log_error "未找到 backend/requirements.txt 文件"
        log_info "项目目录内容:"
        ls -la
        if [ -d "backend" ]; then
            log_info "backend目录内容:"
            ls -la backend/
        fi
        exit 1
    fi
    
    # 检查conda
    if [ ! -f "$CONDA_PATH/bin/conda" ]; then
        log_error "Conda未找到，请确认路径: $CONDA_PATH"
        exit 1
    fi
    
    # 初始化conda
    source $CONDA_PATH/etc/profile.d/conda.sh
    
    # 激活conda环境
    conda activate $CONDA_ENV
    if [ $? -ne 0 ]; then
        log_error "无法激活conda环境: $CONDA_ENV"
        log_info "可用环境列表:"
        conda env list
        exit 1
    fi
    
    log_success "已激活conda环境: $CONDA_ENV"
    
    # 安装基础Python依赖
    log_info "安装基础依赖..."
    pip install -r backend/requirements.txt
    log_success "基础依赖安装完成"
    
    # 安装量化库（可选）
    if [ "$INSTALL_QUANT_LIBS" = "yes" ]; then
        log_info "安装量化库依赖..."
        if [ -f "backend/requirements-open-source.txt" ]; then
            # 优先使用 conda-forge 安装预编译包（避免编译问题）
            log_info "从 conda-forge 安装预编译的核心量化库..."
            
            # 安装需要编译的核心包（使用预编译版本）
            if conda install -y -c conda-forge cvxpy scs osqp clarabel; then
                log_success "核心量化库（预编译版本）安装完成"
                
                # 再用 pip 安装其他纯 Python 包（跳过 OpenBB 避免依赖冲突）
                log_info "安装其他量化库..."
                pip install --no-deps riskfolio-lib PyPortfolioOpt || log_warning "riskfolio-lib/PyPortfolioOpt 安装失败"
                pip install quantstats akshare || log_warning "quantstats/akshare 安装失败"
                
                log_warning "跳过 OpenBB 安装（与 FastAPI 版本冲突）"
                log_success "量化库依赖安装完成（不含 OpenBB）"
                
                # 修复 numpy/pandas 兼容性问题
                log_info "修复 numpy/pandas 兼容性..."
                pip uninstall -y numpy pandas scipy 2>/dev/null || true
                pip install --no-cache-dir numpy==1.26.2 pandas==2.1.3 scipy==1.11.4
                log_success "兼容性问题已修复"
            else
                log_error "conda 安装失败"
                log_warning "可能的解决方案："
                log_warning "1. 升级 GCC: yum install -y centos-release-scl devtoolset-8-gcc*"
                log_warning "2. 或者禁用量化库: 在脚本开头设置 INSTALL_QUANT_LIBS=\"no\""
                
                read -p "是否继续部署（不安装量化库）? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    log_warning "跳过量化库，继续部署..."
                else
                    exit 1
                fi
            fi
        else
            log_warning "未找到 requirements-open-source.txt，跳过量化库安装"
        fi
    else
        log_info "跳过量化库安装（INSTALL_QUANT_LIBS=no）"
    fi
    
    # 配置环境变量
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_info "已创建环境变量文件"
        fi
    fi
}

# 设置前端环境
setup_frontend() {
    log_info "设置前端环境..."
    
    # 确保在项目根目录
    cd $PROJECT_DIR
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js 16+"
        exit 1
    fi
    
    # 检查package.json
    if [ ! -f "frontend/package.json" ]; then
        log_error "未找到 frontend/package.json 文件"
        log_info "frontend目录内容:"
        ls -la frontend/ 2>/dev/null || echo "frontend目录不存在"
        exit 1
    fi
    
    # 进入frontend目录
    cd frontend
    
    # 安装依赖并构建
    npm install
    npm run build
    
    # 返回项目根目录
    cd ..
    log_success "前端构建完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd $PROJECT_DIR/backend
    source $CONDA_PATH/etc/profile.d/conda.sh
    conda activate $CONDA_ENV
    
    # 运行初始化脚本
    if [ -f "scripts/regenerate_tasks.py" ]; then
        python scripts/regenerate_tasks.py
        log_success "待办任务数据已生成"
    fi
    
    if [ -f "scripts/add_dashboard_indexes.py" ]; then
        python scripts/add_dashboard_indexes.py
        log_success "数据库索引已添加"
    fi
}

# 配置systemd服务
setup_services() {
    log_info "配置系统服务..."
    
    # 复制服务文件
    cp $PROJECT_DIR/deploy/fof-backend.service /etc/systemd/system/
    cp $PROJECT_DIR/deploy/fof-frontend.service /etc/systemd/system/
    
    # 重新加载并启用服务
    systemctl daemon-reload
    systemctl enable fof-backend fof-frontend
    
    log_success "系统服务配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 启动后端
    systemctl start fof-backend
    sleep 3
    
    if systemctl is-active --quiet fof-backend; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败"
        journalctl -u fof-backend -n 10
        exit 1
    fi
    
    # 启动前端
    systemctl start fof-frontend
    sleep 2
    
    if systemctl is-active --quiet fof-frontend; then
        log_success "前端服务启动成功"
    else
        log_error "前端服务启动失败"
        journalctl -u fof-frontend -n 10
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
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
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."
    
    sleep 5
    
    # 检查后端API
    if curl -s http://localhost:$BACKEND_PORT/api/v1/health >/dev/null 2>&1; then
        log_success "后端API响应正常"
    else
        log_warning "后端API无响应，请检查日志"
    fi
    
    # 检查前端
    if curl -s -I http://localhost:$FRONTEND_PORT/ | grep -q "200 OK"; then
        log_success "前端页面响应正常"
    else
        log_warning "前端页面无响应，请检查日志"
    fi
}

# 显示部署结果
show_result() {
    echo
    echo "=========================================="
    log_success "🎉 FOF管理平台部署完成！"
    echo "=========================================="
    echo
    log_info "📋 部署信息:"
    echo "  项目路径: $PROJECT_DIR"
    echo "  Git仓库: $GIT_REPO"
    echo "  Conda环境: $CONDA_ENV"
    echo
    log_info "🌐 访问地址:"
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
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
    log_info "📁 重要文件:"
    echo "  数据库: $PROJECT_DIR/backend/fof.db"
    echo "  日志: $PROJECT_DIR/logs/"
    echo "  配置: $PROJECT_DIR/backend/.env"
    echo
    log_info "✨ 新版本特性:"
    echo "  ✅ Dashboard性能优化（加载速度提升80%）"
    echo "  ✅ 火富牛API完整集成（17个接口）"
    echo "  ✅ 因子归因分析数据完整性100%"
    echo "  ✅ 待办任务模块（35个真实任务）"
    echo "  ✅ 新增天市量化1号实盘策略"
    echo
    log_warning "⚠️  重要提醒:"
    echo "  1. 首次访问请使用 Ctrl+Shift+R 强制刷新浏览器"
    echo "  2. 建议定期备份数据库文件"
    echo "  3. 监控服务状态和日志"
    echo
    echo "=========================================="
}

# 主函数
main() {
    echo "=========================================="
    echo "🚀 FOF管理平台一键部署脚本"
    echo "=========================================="
    echo "Git仓库: $GIT_REPO"
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
    
    # 执行部署步骤
    check_root
    check_conda
    install_system_dependencies
    create_directories
    backup_existing
    stop_services
    update_code
    setup_backend
    setup_frontend
    init_database
    setup_services
    start_services
    setup_firewall
    verify_deployment
    show_result
    
    log_success "🎉 部署流程完成！"
}

# 错误处理
trap 'log_error "❌ 部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"