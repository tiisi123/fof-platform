#!/bin/bash

# FOF管理平台业务功能测试脚本
# 测试所有核心业务模块的API接口

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
BACKEND_URL="http://localhost:8506"
API_BASE="$BACKEND_URL/api/v1"
TOKEN=""
TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✓ $1")
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("✗ $1")
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 测试计数
test_start() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# 检查服务状态
check_service() {
    log_info "检查后端服务状态..."
    
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "后端服务运行正常"
        return 0
    else
        log_error "后端服务无响应"
        return 1
    fi
}

# 用户认证测试
test_auth() {
    echo
    echo "=========================================="
    log_info "1. 用户认证模块测试"
    echo "=========================================="
    
    # 测试登录
    test_start
    log_info "测试管理员登录..."
    
    RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"admin","password":"admin123"}')
    
    TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        log_success "管理员登录成功"
        log_info "Token: ${TOKEN:0:20}..."
    else
        log_error "管理员登录失败"
        echo "响应: $RESPONSE"
        return 1
    fi
    
    # 测试获取当前用户信息
    test_start
    log_info "测试获取当前用户信息..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/auth/me" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"username":"admin"'; then
        log_success "获取用户信息成功"
    else
        log_error "获取用户信息失败"
    fi
}

# Dashboard测试
test_dashboard() {
    echo
    echo "=========================================="
    log_info "2. Dashboard模块测试"
    echo "=========================================="
    
    # 测试Dashboard数据
    test_start
    log_info "测试Dashboard数据获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/dashboard/summary" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"total_aum"'; then
        log_success "Dashboard数据获取成功"
        
        # 提取关键指标
        TOTAL_AUM=$(echo $RESPONSE | grep -o '"total_aum":[0-9.]*' | cut -d':' -f2)
        PRODUCT_COUNT=$(echo $RESPONSE | grep -o '"product_count":[0-9]*' | cut -d':' -f2)
        
        log_info "  总规模: $TOTAL_AUM 亿元"
        log_info "  产品数量: $PRODUCT_COUNT 个"
    else
        log_error "Dashboard数据获取失败"
    fi
}

# 产品管理测试
test_products() {
    echo
    echo "=========================================="
    log_info "3. 产品管理模块测试"
    echo "=========================================="
    
    # 测试产品列表
    test_start
    log_info "测试产品列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/products/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "产品列表获取成功"
        
        PRODUCT_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  产品总数: $PRODUCT_COUNT"
    else
        log_error "产品列表获取失败"
    fi
    
    # 测试产品详情
    test_start
    log_info "测试产品详情获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/products/1" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"product_name"'; then
        PRODUCT_NAME=$(echo $RESPONSE | grep -o '"product_name":"[^"]*"' | cut -d'"' -f4)
        log_success "产品详情获取成功: $PRODUCT_NAME"
    else
        log_error "产品详情获取失败"
    fi
}

# 管理人测试
test_managers() {
    echo
    echo "=========================================="
    log_info "4. 管理人模块测试"
    echo "=========================================="
    
    # 测试管理人列表
    test_start
    log_info "测试管理人列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/managers/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "管理人列表获取成功"
        
        MANAGER_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  管理人总数: $MANAGER_COUNT"
    else
        log_error "管理人列表获取失败"
    fi
}

# 净值管理测试
test_nav() {
    echo
    echo "=========================================="
    log_info "5. 净值管理模块测试"
    echo "=========================================="
    
    # 测试净值列表
    test_start
    log_info "测试净值数据获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/nav/?product_id=1&skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "净值数据获取成功"
        
        NAV_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  净值记录数: $NAV_COUNT"
    else
        log_error "净值数据获取失败"
    fi
}

# 持仓管理测试
test_holdings() {
    echo
    echo "=========================================="
    log_info "6. 持仓管理模块测试"
    echo "=========================================="
    
    # 测试持仓列表
    test_start
    log_info "测试持仓数据获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/holdings/?product_id=1" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"' || echo $RESPONSE | grep -q '\[\]'; then
        log_success "持仓数据获取成功"
    else
        log_error "持仓数据获取失败"
    fi
}

# 绩效分析测试
test_analysis() {
    echo
    echo "=========================================="
    log_info "7. 绩效分析模块测试"
    echo "=========================================="
    
    # 测试绩效指标
    test_start
    log_info "测试绩效指标计算..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/analysis/performance?product_id=1" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"total_return"' || echo $RESPONSE | grep -q '"annualized_return"'; then
        log_success "绩效指标计算成功"
    else
        log_error "绩效指标计算失败"
    fi
}

# 因子归因测试
test_attribution() {
    echo
    echo "=========================================="
    log_info "8. 因子归因模块测试"
    echo "=========================================="
    
    # 测试因子归因
    test_start
    log_info "测试因子归因分析..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/attribution/factor-analysis?product_id=1" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"factors"' || echo $RESPONSE | grep -q '"attribution"'; then
        log_success "因子归因分析成功"
    else
        log_error "因子归因分析失败"
    fi
}

# 项目管理测试
test_projects() {
    echo
    echo "=========================================="
    log_info "9. 项目管理模块测试"
    echo "=========================================="
    
    # 测试项目列表
    test_start
    log_info "测试项目列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/projects/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "项目列表获取成功"
        
        PROJECT_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  项目总数: $PROJECT_COUNT"
    else
        log_error "项目列表获取失败"
    fi
}

# 待办任务测试
test_tasks() {
    echo
    echo "=========================================="
    log_info "10. 待办任务模块测试"
    echo "=========================================="
    
    # 测试任务列表
    test_start
    log_info "测试任务列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/tasks/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "任务列表获取成功"
        
        TASK_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  任务总数: $TASK_COUNT"
    else
        log_error "任务列表获取失败"
    fi
}

# 文档管理测试
test_documents() {
    echo
    echo "=========================================="
    log_info "11. 文档管理模块测试"
    echo "=========================================="
    
    # 测试文档列表
    test_start
    log_info "测试文档列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/documents/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "文档列表获取成功"
        
        DOC_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  文档总数: $DOC_COUNT"
    else
        log_error "文档列表获取失败"
    fi
}

# 日历事件测试
test_calendar() {
    echo
    echo "=========================================="
    log_info "12. 日历事件模块测试"
    echo "=========================================="
    
    # 测试日历事件
    test_start
    log_info "测试日历事件获取..."
    
    START_DATE=$(date -d "30 days ago" +%Y-%m-%d)
    END_DATE=$(date -d "30 days" +%Y-%m-%d)
    
    RESPONSE=$(curl -s -X GET "$API_BASE/calendar/events?start_date=$START_DATE&end_date=$END_DATE" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '\[' || echo $RESPONSE | grep -q '"events"'; then
        log_success "日历事件获取成功"
    else
        log_error "日历事件获取失败"
    fi
}

# 审计日志测试
test_audit() {
    echo
    echo "=========================================="
    log_info "13. 审计日志模块测试"
    echo "=========================================="
    
    # 测试审计日志
    test_start
    log_info "测试审计日志获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/audit/logs?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "审计日志获取成功"
        
        LOG_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  日志记录数: $LOG_COUNT"
    else
        log_error "审计日志获取失败"
    fi
}

# 用户管理测试
test_users() {
    echo
    echo "=========================================="
    log_info "14. 用户管理模块测试"
    echo "=========================================="
    
    # 测试用户列表
    test_start
    log_info "测试用户列表获取..."
    
    RESPONSE=$(curl -s -X GET "$API_BASE/users/?skip=0&limit=10" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo $RESPONSE | grep -q '"items"'; then
        log_success "用户列表获取成功"
        
        USER_COUNT=$(echo $RESPONSE | grep -o '"total":[0-9]*' | cut -d':' -f2)
        log_info "  用户总数: $USER_COUNT"
    else
        log_error "用户列表获取失败"
    fi
}

# 显示测试结果
show_results() {
    echo
    echo "=========================================="
    log_info "📊 测试结果汇总"
    echo "=========================================="
    echo
    echo "总测试数: $TOTAL_TESTS"
    echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
    echo -e "${RED}失败: $FAILED_TESTS${NC}"
    echo
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 所有测试通过！${NC}"
        echo
        return 0
    else
        echo -e "${RED}❌ 部分测试失败${NC}"
        echo
        echo "失败的测试:"
        for result in "${TEST_RESULTS[@]}"; do
            if [[ $result == ✗* ]]; then
                echo "  $result"
            fi
        done
        echo
        return 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "🧪 FOF管理平台业务功能测试"
    echo "=========================================="
    echo "后端地址: $BACKEND_URL"
    echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo
    
    # 检查服务
    if ! check_service; then
        log_error "服务未运行，请先启动服务"
        exit 1
    fi
    
    # 执行测试
    test_auth || exit 1
    test_dashboard
    test_products
    test_managers
    test_nav
    test_holdings
    test_analysis
    test_attribution
    test_projects
    test_tasks
    test_documents
    test_calendar
    test_audit
    test_users
    
    # 显示结果
    show_results
}

# 运行测试
main "$@"
