#!/bin/bash

# FOF平台预安装脚本 - 安装系统依赖
# 在运行一键部署脚本之前先运行此脚本

set -e

# 颜色定义
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

echo "=========================================="
echo "🔧 FOF平台预安装脚本"
echo "=========================================="
echo "此脚本将安装编译量化库所需的系统依赖"
echo "包括: gcc, g++, OpenBLAS, LAPACK, CMake"
echo "=========================================="
echo

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    log_error "此脚本需要root权限运行"
    exit 1
fi

# 检测系统类型
if [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    log_info "检测到 CentOS/RHEL 系统"
    OS_TYPE="centos"
    
    log_info "系统信息:"
    cat /etc/redhat-release
    
elif [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    log_info "检测到 Debian/Ubuntu 系统"
    OS_TYPE="debian"
    
    log_info "系统信息:"
    cat /etc/os-release | grep PRETTY_NAME
    
else
    log_error "未识别的系统类型"
    log_info "请手动安装以下依赖:"
    echo "  - gcc/g++ 编译器"
    echo "  - OpenBLAS 开发库"
    echo "  - LAPACK 开发库"
    echo "  - CMake"
    exit 1
fi

echo
read -p "确认开始安装系统依赖? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "安装已取消"
    exit 0
fi

# 安装依赖
if [ "$OS_TYPE" = "centos" ]; then
    log_info "开始安装 CentOS/RHEL 依赖..."
    
    # 安装开发工具
    log_info "1/3 安装开发工具组..."
    yum groupinstall -y "Development Tools" || {
        log_warning "开发工具组安装失败，尝试单独安装..."
        yum install -y gcc gcc-c++ make
    }
    
    # 安装数学库
    log_info "2/3 安装数学库..."
    yum install -y openblas-devel lapack-devel
    
    # 安装CMake
    log_info "3/3 安装 CMake..."
    yum install -y cmake
    
elif [ "$OS_TYPE" = "debian" ]; then
    log_info "开始安装 Debian/Ubuntu 依赖..."
    
    # 更新包列表
    log_info "更新包列表..."
    apt-get update
    
    # 安装依赖
    log_info "1/3 安装编译工具..."
    apt-get install -y build-essential
    
    log_info "2/3 安装数学库..."
    apt-get install -y libopenblas-dev liblapack-dev
    
    log_info "3/3 安装 CMake..."
    apt-get install -y cmake
fi

echo
log_success "✅ 系统依赖安装完成！"
echo

# 验证安装
log_info "验证安装..."
echo

# 检查 gcc
if command -v gcc &> /dev/null; then
    GCC_VERSION=$(gcc --version | head -n1)
    log_success "gcc: $GCC_VERSION"
else
    log_error "gcc 未安装"
fi

# 检查 g++
if command -v g++ &> /dev/null; then
    GPP_VERSION=$(g++ --version | head -n1)
    log_success "g++: $GPP_VERSION"
else
    log_error "g++ 未安装"
fi

# 检查 cmake
if command -v cmake &> /dev/null; then
    CMAKE_VERSION=$(cmake --version | head -n1)
    log_success "cmake: $CMAKE_VERSION"
else
    log_error "cmake 未安装"
fi

# 检查 OpenBLAS
if ldconfig -p 2>/dev/null | grep -q openblas; then
    log_success "OpenBLAS: 已安装"
else
    log_warning "OpenBLAS: 未检测到（可能已安装但未在 ldconfig 缓存中）"
fi

echo
echo "=========================================="
log_success "🎉 预安装完成！"
echo "=========================================="
echo
log_info "下一步:"
echo "  1. 运行部署脚本: bash 一键部署.sh"
echo "  2. 或手动安装 Python 依赖:"
echo "     conda activate py310fof"
echo "     pip install -r backend/requirements.txt"
echo "     pip install -r backend/requirements-open-source.txt"
echo
