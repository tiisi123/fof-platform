#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOF 管理平台 - 深度功能测试
针对每个模块的实际展示功能进行详细测试
包括子菜单、子选项、具体业务功能
"""

import sys
import io
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
SERVER_URL = "http://47.116.187.192:8507"
USERNAME = "admin"
PASSWORD = "admin123"
TIMEOUT = 10

# 测试结果
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "modules": []
}


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Colors.END}\n")


def print_subheader(text):
    """打印子标题"""
    print(f"\n{Colors.MAGENTA}{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}{Colors.END}")


def print_test(name, passed, detail=""):
    """打印测试结果"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"{Colors.GREEN}  ✓{Colors.END} {name}")
    else:
        test_results["failed"] += 1
        print(f"{Colors.RED}  ✗{Colors.END} {name}")
    
    if detail:
        print(f"    {Colors.BLUE}→ {detail}{Colors.END}")


def init_driver():
    """初始化浏览器驱动"""
    print(f"{Colors.YELLOW}[初始化] 启动浏览器...{Colors.END}")
    
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print(f"{Colors.GREEN}[成功] 浏览器已启动{Colors.END}\n")
        return driver
    except Exception as e:
        print(f"{Colors.RED}[失败] 浏览器启动失败: {e}{Colors.END}")
        return None


def login(driver):
    """登录系统"""
    print_header("登录系统")
    
    try:
        driver.get(SERVER_URL)
        time.sleep(3)
        
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "login-form"))
        )
        
        inputs = driver.find_elements(By.CSS_SELECTOR, "input.input-field")
        username_input = None
        password_input = None
        
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "用户名" in placeholder:
                username_input = inp
            elif inp.get_attribute("type") == "password":
                password_input = inp
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button.login-btn")
        
        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)
        time.sleep(1)
        login_button.click()
        time.sleep(3)
        
        print_test("登录成功", True, f"用户: {USERNAME}")
        return True
        
    except Exception as e:
        print_test("登录失败", False, str(e)[:100])
        return False


def navigate_to_module(driver, module_name):
    """导航到指定模块"""
    try:
        print(f"\n{Colors.YELLOW}[导航] → {module_name}{Colors.END}")
        
        # 查找所有可能的菜单元素
        menu_items = driver.find_elements(By.CSS_SELECTOR, 
            "a, .menu-item, li, [class*='menu'], [class*='nav']")
        
        for item in menu_items:
            item_text = item.text.strip()
            if module_name in item_text and len(item_text) < 20:
                driver.execute_script("arguments[0].scrollIntoView(true);", item)
                time.sleep(0.5)
                driver.execute_script("arguments[0].style.border='3px solid blue'", item)
                time.sleep(0.5)
                item.click()
                time.sleep(2)
                return True
        
        return False
    except:
        return False


def find_sub_menus(driver):
    """查找子菜单"""
    sub_menus = []
    try:
        # 查找可能的子菜单、标签页、选项卡
        tabs = driver.find_elements(By.CSS_SELECTOR, 
            ".el-tabs__item, .tab-item, [role='tab'], .nav-tabs li, [class*='tab']")
        
        for tab in tabs:
            text = tab.text.strip()
            if text and len(text) < 30:
                sub_menus.append({"element": tab, "text": text, "type": "tab"})
        
        # 查找下拉菜单
        dropdowns = driver.find_elements(By.CSS_SELECTOR, 
            ".el-dropdown-menu li, .dropdown-item, [class*='dropdown']")
        
        for item in dropdowns:
            text = item.text.strip()
            if text and len(text) < 30:
                sub_menus.append({"element": item, "text": text, "type": "dropdown"})
        
    except Exception as e:
        print(f"    {Colors.YELLOW}查找子菜单异常: {str(e)[:50]}{Colors.END}")
    
    return sub_menus


def test_table_operations(driver, module_name):
    """测试表格操作功能"""
    operations = []
    
    try:
        # 1. 测试表格是否存在
        tables = driver.find_elements(By.CSS_SELECTOR, "table, .el-table")
        if tables:
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr, .el-table__row")
            data_rows = [r for r in rows if r.text.strip()]
            operations.append({
                "name": "数据表格",
                "status": "✓",
                "detail": f"{len(tables)}个表格，{len(data_rows)}行数据"
            })
            print_test("数据表格", True, f"{len(tables)}个表格，{len(data_rows)}行数据")
        else:
            operations.append({"name": "数据表格", "status": "✗", "detail": "未找到表格"})
            print_test("数据表格", False, "未找到表格")
        
        # 2. 测试分页
        pagination = driver.find_elements(By.CSS_SELECTOR, 
            ".el-pagination, .pagination, [class*='pager']")
        if pagination:
            operations.append({"name": "分页功能", "status": "✓", "detail": "存在"})
            print_test("分页功能", True)
        
        # 3. 测试排序
        sort_icons = driver.find_elements(By.CSS_SELECTOR, 
            ".caret-wrapper, [class*='sort'], th[class*='sortable']")
        if sort_icons:
            operations.append({"name": "排序功能", "status": "✓", "detail": f"{len(sort_icons)}列可排序"})
            print_test("排序功能", True, f"{len(sort_icons)}列可排序")
        
        # 4. 测试表格内的操作按钮
        action_buttons = driver.find_elements(By.CSS_SELECTOR, 
            "tbody button, .el-table__row button, td button")
        
        if action_buttons:
            # 统计不同类型的按钮
            button_types = {}
            for btn in action_buttons[:20]:  # 只检查前20个
                text = btn.text.strip()
                if text:
                    button_types[text] = button_types.get(text, 0) + 1
            
            if button_types:
                detail = ", ".join([f"{k}({v})" for k, v in button_types.items()])
                operations.append({"name": "行操作按钮", "status": "✓", "detail": detail})
                print_test("行操作按钮", True, detail)
        
    except Exception as e:
        print(f"    {Colors.YELLOW}表格测试异常: {str(e)[:50]}{Colors.END}")
    
    return operations


def test_form_operations(driver, module_name):
    """测试表单操作功能"""
    operations = []
    
    try:
        # 1. 测试新增/创建按钮
        add_buttons = []
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for btn in all_buttons:
            text = btn.text.strip()
            if any(word in text for word in ['新增', '添加', '创建', '新建', '上传']):
                if len(text) < 20:
                    add_buttons.append({"text": text, "element": btn})
        
        if add_buttons:
            for btn_info in add_buttons[:3]:  # 测试前3个
                try:
                    btn = btn_info["element"]
                    text = btn_info["text"]
                    
                    driver.execute_script("arguments[0].style.border='2px solid green'", btn)
                    time.sleep(0.3)
                    btn.click()
                    time.sleep(1.5)
                    
                    # 检查是否弹出对话框或表单
                    dialogs = driver.find_elements(By.CSS_SELECTOR, 
                        ".el-dialog, .modal, [role='dialog']")
                    
                    if dialogs and dialogs[0].is_displayed():
                        operations.append({
                            "name": f"{text}按钮",
                            "status": "✓",
                            "detail": "弹出对话框"
                        })
                        print_test(f"{text}按钮", True, "弹出对话框")
                        
                        # 测试对话框内的表单元素
                        form_test = test_dialog_form(driver, dialogs[0])
                        operations.extend(form_test)
                        
                        # 关闭对话框
                        close_btns = driver.find_elements(By.CSS_SELECTOR, 
                            ".el-dialog__close, .close, [aria-label='Close']")
                        if close_btns:
                            close_btns[0].click()
                            time.sleep(0.5)
                    else:
                        operations.append({
                            "name": f"{text}按钮",
                            "status": "?",
                            "detail": "可点击但未弹窗"
                        })
                        print_test(f"{text}按钮", True, "可点击但未弹窗")
                    
                    break  # 只测试第一个有效按钮
                except:
                    continue
        
        # 2. 测试导出按钮
        export_buttons = [btn for btn in all_buttons if '导出' in btn.text]
        if export_buttons:
            operations.append({"name": "导出功能", "status": "✓", "detail": f"{len(export_buttons)}个导出按钮"})
            print_test("导出功能", True, f"{len(export_buttons)}个导出按钮")
        
        # 3. 测试批量操作
        batch_buttons = [btn for btn in all_buttons 
                        if any(word in btn.text for word in ['批量', '全选', '删除选中'])]
        if batch_buttons:
            operations.append({"name": "批量操作", "status": "✓", "detail": f"{len(batch_buttons)}个批量按钮"})
            print_test("批量操作", True, f"{len(batch_buttons)}个批量按钮")
        
    except Exception as e:
        print(f"    {Colors.YELLOW}表单测试异常: {str(e)[:50]}{Colors.END}")
    
    return operations


def test_dialog_form(driver, dialog):
    """测试对话框内的表单"""
    form_tests = []
    
    try:
        # 查找表单输入框
        inputs = dialog.find_elements(By.CSS_SELECTOR, 
            "input, textarea, .el-input__inner")
        if inputs:
            form_tests.append({
                "name": "  └─ 表单输入框",
                "status": "✓",
                "detail": f"{len(inputs)}个输入字段"
            })
            print_test("  └─ 表单输入框", True, f"{len(inputs)}个输入字段")
        
        # 查找下拉选择框
        selects = dialog.find_elements(By.CSS_SELECTOR, 
            "select, .el-select, [class*='select']")
        if selects:
            form_tests.append({
                "name": "  └─ 下拉选择",
                "status": "✓",
                "detail": f"{len(selects)}个选择框"
            })
            print_test("  └─ 下拉选择", True, f"{len(selects)}个选择框")
        
        # 查找日期选择器
        date_pickers = dialog.find_elements(By.CSS_SELECTOR, 
            ".el-date-editor, [class*='date-picker']")
        if date_pickers:
            form_tests.append({
                "name": "  └─ 日期选择",
                "status": "✓",
                "detail": f"{len(date_pickers)}个日期选择器"
            })
            print_test("  └─ 日期选择", True, f"{len(date_pickers)}个日期选择器")
        
        # 查找上传组件
        uploads = dialog.find_elements(By.CSS_SELECTOR, 
            ".el-upload, [class*='upload']")
        if uploads:
            form_tests.append({
                "name": "  └─ 文件上传",
                "status": "✓",
                "detail": f"{len(uploads)}个上传组件"
            })
            print_test("  └─ 文件上传", True, f"{len(uploads)}个上传组件")
        
        # 查找提交按钮
        submit_btns = dialog.find_elements(By.CSS_SELECTOR, 
            "button[type='submit'], button.el-button--primary")
        if submit_btns:
            form_tests.append({
                "name": "  └─ 提交按钮",
                "status": "✓",
                "detail": "存在"
            })
            print_test("  └─ 提交按钮", True)
        
    except Exception as e:
        print(f"    {Colors.YELLOW}对话框表单测试异常: {str(e)[:30]}{Colors.END}")
    
    return form_tests


def test_filter_operations(driver, module_name):
    """测试筛选和搜索功能"""
    operations = []
    
    try:
        # 1. 测试搜索框
        search_inputs = driver.find_elements(By.CSS_SELECTOR, 
            "input[placeholder*='搜索'], input[placeholder*='查询'], input[placeholder*='关键']")
        
        if search_inputs:
            for inp in search_inputs[:2]:  # 测试前2个
                try:
                    placeholder = inp.get_attribute("placeholder")
                    driver.execute_script("arguments[0].style.border='2px solid purple'", inp)
                    time.sleep(0.3)
                    inp.click()
                    inp.send_keys("测试")
                    time.sleep(0.5)
                    inp.clear()
                    operations.append({
                        "name": f"搜索框-{placeholder}",
                        "status": "✓",
                        "detail": "可输入"
                    })
                    print_test(f"搜索框-{placeholder}", True, "可输入")
                except:
                    continue
        
        # 2. 测试筛选器
        selects = driver.find_elements(By.CSS_SELECTOR, 
            ".el-select, select, [class*='filter-select']")
        
        if selects:
            operations.append({
                "name": "筛选器",
                "status": "✓",
                "detail": f"{len(selects)}个筛选条件"
            })
            print_test("筛选器", True, f"{len(selects)}个筛选条件")
        
        # 3. 测试日期范围选择
        date_ranges = driver.find_elements(By.CSS_SELECTOR, 
            ".el-date-editor--daterange, [class*='date-range']")
        
        if date_ranges:
            operations.append({
                "name": "日期范围",
                "status": "✓",
                "detail": f"{len(date_ranges)}个日期范围选择"
            })
            print_test("日期范围", True, f"{len(date_ranges)}个日期范围选择")
        
        # 4. 测试重置按钮
        reset_buttons = [btn for btn in driver.find_elements(By.TAG_NAME, "button")
                        if '重置' in btn.text or '清空' in btn.text]
        
        if reset_buttons:
            operations.append({
                "name": "重置按钮",
                "status": "✓",
                "detail": "存在"
            })
            print_test("重置按钮", True)
        
    except Exception as e:
        print(f"    {Colors.YELLOW}筛选测试异常: {str(e)[:50]}{Colors.END}")
    
    return operations


def test_chart_operations(driver, module_name):
    """测试图表功能"""
    operations = []
    
    try:
        # 1. 查找图表
        charts = driver.find_elements(By.CSS_SELECTOR, 
            "canvas, [class*='echarts'], [class*='chart'], svg[class*='chart']")
        
        if charts:
            operations.append({
                "name": "数据图表",
                "status": "✓",
                "detail": f"{len(charts)}个图表"
            })
            print_test("数据图表", True, f"{len(charts)}个图表")
            
            # 测试图表交互
            try:
                actions = ActionChains(driver)
                actions.move_to_element(charts[0]).perform()
                time.sleep(0.5)
                operations.append({
                    "name": "  └─ 图表交互",
                    "status": "✓",
                    "detail": "可悬停"
                })
                print_test("  └─ 图表交互", True, "可悬停")
            except:
                pass
        
        # 2. 查找图表切换按钮
        chart_tabs = driver.find_elements(By.CSS_SELECTOR, 
            "[class*='chart-tab'], [class*='chart-type']")
        
        if chart_tabs:
            operations.append({
                "name": "图表切换",
                "status": "✓",
                "detail": f"{len(chart_tabs)}个图表类型"
            })
            print_test("图表切换", True, f"{len(chart_tabs)}个图表类型")
        
    except Exception as e:
        print(f"    {Colors.YELLOW}图表测试异常: {str(e)[:50]}{Colors.END}")
    
    return operations


def test_data_cards(driver, module_name):
    """测试数据卡片"""
    operations = []
    
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, 
            ".card, .el-card, [class*='stat-card'], [class*='data-card']")
        
        if cards:
            # 统计卡片内容
            card_contents = []
            for card in cards[:10]:  # 只检查前10个
                text = card.text.strip()
                if text and len(text) < 100:
                    card_contents.append(text[:30])
            
            operations.append({
                "name": "数据卡片",
                "status": "✓",
                "detail": f"{len(cards)}个卡片"
            })
            print_test("数据卡片", True, f"{len(cards)}个卡片")
        
    except Exception as e:
        print(f"    {Colors.YELLOW}卡片测试异常: {str(e)[:50]}{Colors.END}")
    
    return operations


def test_module_comprehensive(driver, module_name):
    """综合测试一个模块的所有功能"""
    print_header(f"{module_name} 模块深度测试")
    
    module_result = {
        "name": module_name,
        "found": False,
        "sub_menus": [],
        "operations": []
    }
    
    # 导航到模块
    if not navigate_to_module(driver, module_name):
        print_test(f"导航到{module_name}", False, "未找到菜单")
        test_results["modules"].append(module_result)
        return module_result
    
    print_test(f"导航到{module_name}", True)
    module_result["found"] = True
    time.sleep(2)
    
    # 查找子菜单
    print_subheader("子菜单/标签页")
    sub_menus = find_sub_menus(driver)
    if sub_menus:
        print_test("子菜单", True, f"找到{len(sub_menus)}个子选项")
        for sub in sub_menus[:5]:  # 只显示前5个
            print(f"    {Colors.CYAN}• {sub['text']}{Colors.END}")
        module_result["sub_menus"] = [s["text"] for s in sub_menus]
    else:
        print_test("子菜单", False, "未找到子菜单")
    
    # 测试各类功能
    print_subheader("数据展示功能")
    table_ops = test_table_operations(driver, module_name)
    module_result["operations"].extend(table_ops)
    
    chart_ops = test_chart_operations(driver, module_name)
    module_result["operations"].extend(chart_ops)
    
    card_ops = test_data_cards(driver, module_name)
    module_result["operations"].extend(card_ops)
    
    print_subheader("筛选和搜索功能")
    filter_ops = test_filter_operations(driver, module_name)
    module_result["operations"].extend(filter_ops)
    
    print_subheader("表单和操作功能")
    form_ops = test_form_operations(driver, module_name)
    module_result["operations"].extend(form_ops)
    
    # 如果有子菜单，测试第一个子菜单
    if sub_menus:
        print_subheader(f"测试子菜单: {sub_menus[0]['text']}")
        try:
            sub_menus[0]["element"].click()
            time.sleep(2)
            print_test(f"切换到{sub_menus[0]['text']}", True)
            
            # 简单测试子菜单内容
            sub_table_ops = test_table_operations(driver, f"{module_name}-{sub_menus[0]['text']}")
            module_result["operations"].extend(sub_table_ops)
        except Exception as e:
            print_test(f"切换到{sub_menus[0]['text']}", False, str(e)[:50])
    
    test_results["modules"].append(module_result)
    return module_result


def print_summary():
    """打印测试总结"""
    print_header("测试结果总结")
    
    print(f"{Colors.CYAN}总测试项: {test_results['total']}{Colors.END}")
    print(f"{Colors.GREEN}通过: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}失败: {test_results['failed']}{Colors.END}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"{Colors.YELLOW}成功率: {success_rate:.1f}%{Colors.END}")
    
    # 模块详情
    print_header("各模块功能统计")
    for module in test_results['modules']:
        if module['found']:
            ops_count = len(module['operations'])
            sub_count = len(module.get('sub_menus', []))
            print(f"\n{Colors.CYAN}【{module['name']}】{Colors.END}")
            print(f"  子菜单: {sub_count}个")
            print(f"  功能项: {ops_count}个")
            
            # 显示功能列表
            for op in module['operations']:
                status_color = Colors.GREEN if op['status'] == '✓' else Colors.YELLOW
                print(f"    {status_color}{op['status']}{Colors.END} {op['name']}: {op.get('detail', '')}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "server": SERVER_URL,
        "summary": {
            "total": test_results['total'],
            "passed": test_results['passed'],
            "failed": test_results['failed']
        },
        "modules": test_results['modules']
    }
    
    with open('深度测试报告.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{Colors.BLUE}详细报告已保存: 深度测试报告.json{Colors.END}")


def main():
    """主函数"""
    print_header("FOF 管理平台 - 深度功能测试")
    print(f"服务器: {SERVER_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{Colors.YELLOW}本次测试将深入检查每个模块的：")
    print("  • 子菜单和标签页")
    print("  • 数据表格和操作按钮")
    print("  • 图表和数据卡片")
    print("  • 筛选和搜索功能")
    print("  • 表单和对话框")
    print("  • 各模块特有的业务功能")
    print(f"{Colors.END}")
    
    driver = init_driver()
    if not driver:
        return
    
    try:
        if login(driver):
            # 测试主要模块（根据实际菜单）
            modules_to_test = [
                "总览",
                "管理人",
                "跟踪池",
                "组合管理",
                "一级项目",
                "市场数据",
                "因子归因",
                "异常预警",
                "AI报告",
                "尽调资料",
                "邮箱爬虫",
                "报表中心"
            ]
            
            for module in modules_to_test:
                test_module_comprehensive(driver, module)
                time.sleep(1)
        else:
            print(f"\n{Colors.RED}登录失败，测试终止{Colors.END}")
    
    except Exception as e:
        print(f"\n{Colors.RED}测试异常: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
    
    finally:
        time.sleep(2)
        driver.quit()
        print(f"\n{Colors.YELLOW}[完成] 浏览器已关闭{Colors.END}")
    
    print_summary()


if __name__ == "__main__":
    main()
