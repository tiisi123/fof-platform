#!/bin/bash
# FOF 管理平台功能检测脚本
# 用途：检测部署后所有功能是否正常

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
BACKEND_URL="http://localhost:8506"
FRONTEND_URL="http://localhost:8507"
API_BASE="${BACKEND_URL}/api/v1"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 测试 HTTP 请求
test_http() {
    local url=$1
    local method=${2:-GET}
    local data=${3:-}
    local token=${4:-}
    local expected_code=${5:-200}
    
    local headers=""
    if [ -n "$token" ]; then
        headers="-H 'Authorization: Bearer $token'"
    fi
    
    if [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        headers="$headers -H 'Content-Type: application/json'"
    fi
    
    local cmd="curl -s -w '\n%{http_code}' -X $method $headers"
    if [ -n "$data" ]; then
        cmd="$cmd -d '$data'"
    fi
    cmd="$cmd '$url'"
    
    local response=$(eval $cmd)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        return 0
    else
        return 1
    fi
}

# 分隔线
print_separator() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# 1. 基础服务检测
test_basic_services() {
    print_separator "1. 基础服务检测"
    
    # 检测后端服务
    log_info "检测后端服务..."
    if systemctl is-active --quiet fof-backend; then
        log_success "后端服务运行中"
    else
        log_error "后端服务未运行"
    fi
    
    # 检测前端服务
    log_info "检测前端服务..."
    if systemctl is-active --quiet fof-frontend; then
        log_success "前端服务运行中"
    else
        log_error "前端服务未运行"
    fi
    
    # 检测后端端口
    log_info "检测后端端口 8506..."
    if netstat -tuln | grep -q ":8506 "; then
        log_success "后端端口 8506 监听中"
    else
        log_error "后端端口 8506 未监听"
    fi
    
    # 检测前端端口
    log_info "检测前端端口 8507..."
    if netstat -tuln | grep -q ":8507 "; then
        log_success "前端端口 8507 监听中"
    else
        log_error "前端端口 8507 未监听"
    fi
}

# 2. 后端 API 检测
test_backend_api() {
    print_separator "2. 后端 API 检测"
    
    # 健康检查
    log_info "测试健康检查接口..."
    if test_http "${BACKEND_URL}/health"; then
        log_success "健康检查接口正常"
    else
        log_error "健康检查接口失败"
    fi
    
    # 根路径
    log_info "测试根路径..."
    if test_http "${BACKEND_URL}/"; then
        log_success "根路径访问正常"
    else
        log_error "根路径访问失败"
    fi
    
    # API 文档
    log_info "测试 API 文档..."
    if test_http "${BACKEND_URL}/api/docs"; then
        log_success "API 文档访问正常"
    else
        log_error "API 文档访问失败"
    fi
}

# 3. 认证功能检测
test_auth() {
    print_separator "3. 认证功能检测"
    
    # 登录接口
    log_info "测试登录接口..."
    local login_data='{"username":"admin","password":"admin123"}'
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$login_data" \
        "${API_BASE}/auth/login")
    
    if echo "$response" | grep -q "access_token"; then
        log_success "登录接口正常"
        # 提取 token 用于后续测试
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        export TOKEN
    else
        log_error "登录接口失败"
        TOKEN=""
    fi
}

# 4. 核心功能模块检测
test_core_modules() {
    print_separator "4. 核心功能模块检测"
    
    if [ -z "$TOKEN" ]; then
        log_warning "未获取到 Token，跳过需要认证的接口测试"
        return
    fi
    
    # 管理人列表
    log_info "测试管理人列表接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/managers/" | grep -q "\["; then
        log_success "管理人列表接口正常"
    else
        log_error "管理人列表接口失败"
    fi
    
    # 产品列表
    log_info "测试产品列表接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/products/" | grep -q "\["; then
        log_success "产品列表接口正常"
    else
        log_error "产品列表接口失败"
    fi
    
    # 净值列表
    log_info "测试净值列表接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/nav/" | grep -q "\["; then
        log_success "净值列表接口正常"
    else
        log_error "净值列表接口失败"
    fi
    
    # 项目列表
    log_info "测试项目列表接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/projects/" | grep -q "\["; then
        log_success "项目列表接口正常"
    else
        log_error "项目列表接口失败"
    fi
    
    # 用户列表
    log_info "测试用户列表接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/users/" | grep -q "\["; then
        log_success "用户列表接口正常"
    else
        log_error "用户列表接口失败"
    fi
    
    # 仪表盘
    log_info "测试仪表盘接口..."
    if curl -s -H "Authorization: Bearer $TOKEN" \
        "${API_BASE}/dashboard/summary" | grep -q "{"; then
        log_success "仪表盘接口正常"
    else
        log_error "仪表盘接口失败"
    fi
}

# 5. 前端页面检测
test_frontend() {
    print_separator "5. 前端页面检测"
    
    # 首页
    log_info "测试前端首页..."
    if curl -s "${FRONTEND_URL}/" | grep -q "<!DOCTYPE html>"; then
        log_success "前端首页访问正常"
    else
        log_error "前端首页访问失败"
    fi
    
    # 静态资源
    log_info "测试静态资源..."
    if curl -s "${FRONTEND_URL}/index.html" | grep -q "<!DOCTYPE html>"; then
        log_success "静态资源访问正常"
    else
        log_error "静态资源访问失败"
    fi
}

# 6. 数据库检测
test_database() {
    print_separator "6. 数据库检测"
    
    local db_file="/root/web/fof/backend/fof.db"
    
    # 检测数据库文件
    log_info "检测数据库文件..."
    if [ -f "$db_file" ]; then
        log_success "数据库文件存在"
        
        # 检测数据库大小
        local db_size=$(du -h "$db_file" | cut -f1)
        log_info "数据库大小: $db_size"
        
        # 检测数据库表
        log_info "检测数据库表..."
        local table_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
        if [ "$table_count" -gt 0 ]; then
            log_success "数据库包含 $table_count 个表"
        else
            log_error "数据库表为空"
        fi
    else
        log_error "数据库文件不存在"
    fi
}

# 7. 日志检测
test_logs() {
    print_separator "7. 日志检测"
    
    local log_dir="/root/web/fof/logs"
    
    # 检测日志目录
    log_info "检测日志目录..."
    if [ -d "$log_dir" ]; then
        log_success "日志目录存在"
        
        # 检测后端日志
        if [ -f "$log_dir/backend.log" ]; then
            log_success "后端日志文件存在"
            local backend_log_size=$(du -h "$log_dir/backend.log" | cut -f1)
            log_info "后端日志大小: $backend_log_size"
        else
            log_warning "后端日志文件不存在"
        fi
        
        # 检测前端日志
        if [ -f "$log_dir/frontend.log" ]; then
            log_success "前端日志文件存在"
            local frontend_log_size=$(du -h "$log_dir/frontend.log" | cut -f1)
            log_info "前端日志大小: $frontend_log_size"
        else
            log_warning "前端日志文件不存在"
        fi
        
        # 检测错误日志
        log_info "检测最近的错误日志..."
        local error_count=$(grep -i "error" "$log_dir"/*.log 2>/dev/null | tail -5 | wc -l)
        if [ "$error_count" -gt 0 ]; then
            log_warning "发现 $error_count 条最近的错误日志"
            echo "最近的错误："
            grep -i "error" "$log_dir"/*.log 2>/dev/null | tail -5
        else
            log_success "未发现最近的错误日志"
        fi
    else
        log_error "日志目录不存在"
    fi
}

# 8. 环境配置检测
test_environment() {
    print_separator "8. 环境配置检测"
    
    # 检测 Python 环境
    log_info "检测 Python 环境..."
    if conda env list | grep -q "py310fof"; then
        log_success "Conda 环境 py310fof 存在"
    else
        log_error "Conda 环境 py310fof 不存在"
    fi
    
    # 检测环境变量文件
    log_info "检测环境变量文件..."
    if [ -f "/root/web/fof/backend/.env" ]; then
        log_success "环境变量文件存在"
    else
        log_error "环境变量文件不存在"
    fi
    
    # 检测上传目录
    log_info "检测上传目录..."
    if [ -d "/root/web/fof/backend/uploads" ]; then
        log_success "上传目录存在"
    else
        log_warning "上传目录不存在"
    fi
}

# 9. 性能检测
test_performance() {
    print_separator "9. 性能检测"
    
    # 测试响应时间
    log_info "测试 API 响应时间..."
    local start_time=$(date +%s%N)
    curl -s "${BACKEND_URL}/health" > /dev/null
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$response_time" -lt 1000 ]; then
        log_success "API 响应时间: ${response_time}ms (优秀)"
    elif [ "$response_time" -lt 3000 ]; then
        log_success "API 响应时间: ${response_time}ms (良好)"
    else
        log_warning "API 响应时间: ${response_time}ms (较慢)"
    fi
    
    # 检测内存使用
    log_info "检测服务内存使用..."
    local backend_mem=$(ps aux | grep "uvicorn" | grep -v grep | awk '{print $6}' | head -1)
    if [ -n "$backend_mem" ]; then
        backend_mem_mb=$((backend_mem / 1024))
        log_info "后端服务内存使用: ${backend_mem_mb}MB"
    fi
    
    local frontend_mem=$(ps aux | grep "http-server" | grep -v grep | awk '{print $6}' | head -1)
    if [ -n "$frontend_mem" ]; then
        frontend_mem_mb=$((frontend_mem / 1024))
        log_info "前端服务内存使用: ${frontend_mem_mb}MB"
    fi
}

# 10. 安全检测
test_security() {
    print_separator "10. 安全检测"
    
    # 检测文件权限
    log_info "检测敏感文件权限..."
    local env_file="/root/web/fof/backend/.env"
    if [ -f "$env_file" ]; then
        local env_perm=$(stat -c "%a" "$env_file")
        if [ "$env_perm" = "600" ] || [ "$env_perm" = "400" ]; then
            log_success "环境变量文件权限安全 ($env_perm)"
        else
            log_warning "环境变量文件权限不够安全 ($env_perm)，建议设置为 600"
        fi
    fi
    
    # 检测数据库权限
    local db_file="/root/web/fof/backend/fof.db"
    if [ -f "$db_file" ]; then
        local db_perm=$(stat -c "%a" "$db_file")
        if [ "$db_perm" = "600" ] || [ "$db_perm" = "400" ]; then
            log_success "数据库文件权限安全 ($db_perm)"
        else
            log_warning "数据库文件权限不够安全 ($db_perm)，建议设置为 600"
        fi
    fi
    
    # 检测防火墙
    log_info "检测防火墙状态..."
    if systemctl is-active --quiet firewalld; then
        log_success "防火墙运行中"
    else
        log_warning "防火墙未运行"
    fi
}

# 主函数
main() {
    echo ""
    echo "======================================"
    echo "  FOF 管理平台功能检测"
    echo "======================================"
    echo ""
    
    # 执行所有测试
    test_basic_services
    test_backend_api
    test_auth
    test_core_modules
    test_frontend
    test_database
    test_logs
    test_environment
    test_performance
    test_security
    
    # 输出测试结果
    print_separator "测试结果汇总"
    echo ""
    echo "总测试数: $TOTAL_TESTS"
    echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
    echo -e "${RED}失败: $FAILED_TESTS${NC}"
    echo ""
    
    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✓ 所有测试通过！系统运行正常。${NC}"
        exit 0
    else
        echo -e "${RED}✗ 有 $FAILED_TESTS 个测试失败，请检查日志。${NC}"
        exit 1
    fi
}

# 运行主函数
main
