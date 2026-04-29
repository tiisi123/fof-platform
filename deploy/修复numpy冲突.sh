#!/bin/bash

# 修复 numpy/pandas 二进制不兼容问题

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
echo "🔧 修复 numpy/pandas 兼容性问题"
echo "=========================================="
echo "错误: numpy.dtype size changed"
echo "原因: conda 和 pip 包版本冲突"
echo "=========================================="
echo

# 激活环境
log_info "激活 conda 环境..."
source $CONDA_PATH/etc/profile.d/conda.sh
conda activate $CONDA_ENV

if [ $? -ne 0 ]; then
    log_error "无法激活环境: $CONDA_ENV"
    exit 1
fi

log_success "环境已激活"
echo

# 显示当前版本
log_info "当前版本:"
python -c "import numpy; print('numpy:', numpy.__version__)" 2>/dev/null || echo "numpy: 未安装或损坏"
python -c "import pandas; print('pandas:', pandas.__version__)" 2>/dev/null || echo "pandas: 未安装或损坏"
echo

# 方案选择
echo "请选择修复方案:"
echo "  1) 重新安装 numpy 和 pandas（推荐）"
echo "  2) 重建整个 conda 环境（彻底解决）"
echo "  3) 仅重新编译 pandas"
echo
read -p "请选择 (1/2/3): " -n 1 -r
echo
echo

case $REPLY in
    1)
        log_info "方案1: 重新安装 numpy 和 pandas"
        echo
        
        # 停止服务
        log_info "停止后端服务..."
        systemctl stop fof-backend 2>/dev/null || true
        
        # 卸载
        log_info "卸载现有的 numpy 和 pandas..."
        pip uninstall -y numpy pandas scipy 2>/dev/null || true
        conda uninstall -y numpy pandas scipy --force 2>/dev/null || true
        
        # 重新安装（使用 pip，确保版本一致）
        log_info "重新安装 numpy, pandas, scipy..."
        pip install --no-cache-dir numpy==1.26.2
        pip install --no-cache-dir pandas==2.1.3
        pip install --no-cache-dir scipy==1.11.4
        
        # 验证
        log_info "验证安装..."
        python -c "import numpy; print('✅ numpy:', numpy.__version__)"
        python -c "import pandas; print('✅ pandas:', pandas.__version__)"
        python -c "import scipy; print('✅ scipy:', scipy.__version__)"
        
        # 测试导入
        log_info "测试导入..."
        python -c "import pandas as pd; df = pd.DataFrame({'a': [1,2,3]}); print('✅ pandas 工作正常')"
        
        log_success "修复完成！"
        ;;
        
    2)
        log_info "方案2: 重建 conda 环境"
        echo
        
        log_warning "这将删除并重建整个环境，需要重新安装所有依赖"
        read -p "确认继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "取消操作"
            exit 0
        fi
        
        # 停止服务
        systemctl stop fof-backend fof-frontend 2>/dev/null || true
        
        # 导出已安装的包
        log_info "导出包列表..."
        pip list --format=freeze > /tmp/pip-backup-$(date +%Y%m%d_%H%M%S).txt
        
        # 删除环境
        log_info "删除旧环境..."
        conda deactivate 2>/dev/null || true
        conda env remove -n $CONDA_ENV -y
        
        # 创建新环境
        log_info "创建新环境..."
        conda create -n $CONDA_ENV python=3.10 -y
        conda activate $CONDA_ENV
        
        # 安装依赖
        log_info "安装项目依赖..."
        cd /root/web/fof
        pip install -r backend/requirements.txt
        
        log_success "环境重建完成！"
        log_info "请重新运行部署脚本安装量化库"
        ;;
        
    3)
        log_info "方案3: 重新编译 pandas"
        echo
        
        # 停止服务
        systemctl stop fof-backend 2>/dev/null || true
        
        # 重新安装 pandas
        log_info "重新安装 pandas..."
        pip uninstall -y pandas
        pip install --no-cache-dir --force-reinstall pandas==2.1.3
        
        # 验证
        python -c "import pandas; print('✅ pandas:', pandas.__version__)"
        
        log_success "修复完成！"
        ;;
        
    *)
        log_error "无效选择"
        exit 1
        ;;
esac

echo
echo "=========================================="
log_success "🎉 修复完成！"
echo "=========================================="
echo

# 重启服务
log_info "重启后端服务..."
systemctl start fof-backend

sleep 3

if systemctl is-active --quiet fof-backend; then
    log_success "✅ 后端服务启动成功！"
    echo
    log_info "查看服务状态:"
    systemctl status fof-backend --no-pager -l
else
    log_error "❌ 后端服务启动失败"
    echo
    log_info "查看错误日志:"
    journalctl -u fof-backend -n 30 --no-pager
    exit 1
fi

echo
log_info "测试 API:"
sleep 2
curl -s http://localhost:8506/api/v1/health && echo " ✅ API 正常" || echo " ❌ API 无响应"
