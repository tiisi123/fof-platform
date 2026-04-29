#!/bin/bash

# 清理 OpenBB 及其依赖，避免版本冲突

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

CONDA_PATH="/root/anaconda3"
CONDA_ENV="py310fof"

echo "=========================================="
echo "🧹 清理 OpenBB"
echo "=========================================="
echo "OpenBB 与项目的 FastAPI 版本冲突"
echo "将卸载 OpenBB 及其相关包"
echo "=========================================="
echo

# 激活环境
source $CONDA_PATH/etc/profile.d/conda.sh
conda activate $CONDA_ENV

log_info "当前已安装的 OpenBB 相关包:"
pip list | grep -i openbb || echo "未找到 OpenBB 包"
echo

read -p "确认卸载 OpenBB? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "取消操作"
    exit 0
fi

log_info "卸载 OpenBB 及其依赖..."

# 卸载 OpenBB 相关包
pip uninstall -y openbb openbb-core openbb-federal-reserve openbb-us-eia 2>/dev/null || true

log_success "OpenBB 已卸载"
echo

log_info "验证核心依赖版本:"
echo "FastAPI: $(pip show fastapi | grep Version | cut -d' ' -f2)"
echo "Pydantic: $(pip show pydantic | grep Version | cut -d' ' -f2)"
echo "Uvicorn: $(pip show uvicorn | grep Version | cut -d' ' -f2)"
echo

log_info "已安装的量化库:"
python -c "import cvxpy; print('✅ cvxpy:', cvxpy.__version__)" 2>/dev/null || echo "❌ cvxpy"
python -c "import riskfolio; print('✅ riskfolio-lib:', riskfolio.__version__)" 2>/dev/null || echo "❌ riskfolio-lib"
python -c "import pypfopt; print('✅ PyPortfolioOpt:', pypfopt.__version__)" 2>/dev/null || echo "❌ PyPortfolioOpt"
python -c "import quantstats; print('✅ quantstats:', quantstats.__version__)" 2>/dev/null || echo "❌ quantstats"
python -c "import akshare; print('✅ akshare:', akshare.__version__)" 2>/dev/null || echo "❌ akshare"

echo
log_success "✅ 清理完成！"
log_info "建议重启后端服务: systemctl restart fof-backend"
