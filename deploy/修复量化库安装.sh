#!/bin/bash

# 修复量化库安装问题
# 使用 conda 预编译版本避免 GCC 版本问题

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

CONDA_PATH="/root/anaconda3"
CONDA_ENV="py310fof"

echo "=========================================="
echo "🔧 修复量化库安装"
echo "=========================================="
echo "使用 conda 预编译版本避免编译问题"
echo "=========================================="
echo

# 检查 conda
if [ ! -f "$CONDA_PATH/bin/conda" ]; then
    log_error "Conda 未找到: $CONDA_PATH"
    exit 1
fi

# 初始化 conda
source $CONDA_PATH/etc/profile.d/conda.sh

# 激活环境
log_info "激活 conda 环境: $CONDA_ENV"
conda activate $CONDA_ENV

if [ $? -ne 0 ]; then
    log_error "无法激活环境: $CONDA_ENV"
    conda env list
    exit 1
fi

log_success "环境已激活"
echo

# 显示当前 GCC 版本
log_info "当前 GCC 版本:"
gcc --version | head -n1
echo

# 方案选择
echo "请选择安装方案:"
echo "  1) 使用 conda 预编译版本（推荐，无需编译）"
echo "  2) 升级 GCC 后编译安装（需要 CentOS 7+）"
echo "  3) 跳过量化库安装"
echo
read -p "请选择 (1/2/3): " -n 1 -r
echo
echo

case $REPLY in
    1)
        log_info "方案1: 使用 conda 预编译版本"
        echo
        
        # 安装核心编译包（预编译版本）
        log_info "安装核心量化库（预编译）..."
        conda install -y -c conda-forge cvxpy scs osqp clarabel
        
        if [ $? -eq 0 ]; then
            log_success "核心库安装成功"
            echo
            
            # 安装其他纯 Python 包
            log_info "安装其他量化库..."
            
            # 单独安装每个包，避免依赖冲突
            pip install --no-deps riskfolio-lib || log_warning "riskfolio-lib 安装失败"
            pip install --no-deps PyPortfolioOpt || log_warning "PyPortfolioOpt 安装失败"
            pip install quantstats || log_warning "quantstats 安装失败"
            pip install akshare || log_warning "akshare 安装失败"
            
            log_warning "跳过 OpenBB（与项目 FastAPI 版本冲突）"
            
            echo
            log_success "✅ 量化库安装完成（不含 OpenBB）！"
        else
            log_error "安装失败"
            exit 1
        fi
        ;;
        
    2)
        log_info "方案2: 升级 GCC 后编译安装"
        echo
        
        # 检查是否为 CentOS 7+
        if [ ! -f /etc/redhat-release ]; then
            log_error "此方案仅支持 CentOS/RHEL"
            exit 1
        fi
        
        log_info "安装 devtoolset-8..."
        yum install -y centos-release-scl
        yum install -y devtoolset-8-gcc devtoolset-8-gcc-c++
        
        log_info "启用新版 GCC..."
        source /opt/rh/devtoolset-8/enable
        
        log_info "新的 GCC 版本:"
        gcc --version | head -n1
        echo
        
        log_info "编译安装量化库..."
        cd /root/web/fof
        pip install -r backend/requirements-open-source.txt
        
        if [ $? -eq 0 ]; then
            log_success "✅ 量化库安装完成！"
            log_warning "注意: 每次使用前需要运行: source /opt/rh/devtoolset-8/enable"
        else
            log_error "安装失败"
            exit 1
        fi
        ;;
        
    3)
        log_info "方案3: 跳过量化库安装"
        log_warning "量化分析功能将不可用"
        log_info "可以编辑 一键部署.sh，设置 INSTALL_QUANT_LIBS=\"no\""
        exit 0
        ;;
        
    *)
        log_error "无效选择"
        exit 1
        ;;
esac

echo
echo "=========================================="
log_success "🎉 完成！"
echo "=========================================="
echo

# 验证安装
log_info "验证安装..."
echo

python -c "import cvxpy; print('✅ cvxpy:', cvxpy.__version__)" 2>/dev/null || echo "❌ cvxpy 未安装"
python -c "import scs; print('✅ scs:', scs.__version__)" 2>/dev/null || echo "❌ scs 未安装"
python -c "import riskfolio; print('✅ riskfolio-lib:', riskfolio.__version__)" 2>/dev/null || echo "❌ riskfolio-lib 未安装"
python -c "import pypfopt; print('✅ PyPortfolioOpt:', pypfopt.__version__)" 2>/dev/null || echo "❌ PyPortfolioOpt 未安装"
python -c "import quantstats; print('✅ quantstats:', quantstats.__version__)" 2>/dev/null || echo "❌ quantstats 未安装"
python -c "import akshare; print('✅ akshare:', akshare.__version__)" 2>/dev/null || echo "❌ akshare 未安装"

echo
log_info "下一步: 重启后端服务"
echo "  systemctl restart fof-backend"
echo
