#!/usr/bin/env python3
"""
FOF管理平台业务逻辑深度测试
验证业务功能的正确性、数据准确性、逻辑完整性
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# 配置
SERVER_IP = "47.116.187.192"
BACKEND_PORT = "8506"
BACKEND_URL = f"http://{SERVER_IP}:{BACKEND_PORT}"
API_BASE = f"{BACKEND_URL}/api/v1"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

class BusinessLogicTester:
    def __init__(self):
        self.token = None
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.test_results = []
        
    def log_info(self, msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    def log_success(self, msg: str):
        print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")
        self.passed += 1
        self.test_results.append(("PASS", msg))
    
    def log_error(self, msg: str, detail: str = ""):
        print(f"{Colors.RED}[✗]{Colors.NC} {msg}")
        if detail:
            print(f"  详情: {detail}")
        self.failed += 1
        self.test_results.append(("FAIL", msg, detail))
    
    def log_warning(self, msg: str):
        print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")
    
    def assert_equal(self, actual, expected, test_name: str):
        """断言相等"""
        self.total += 1
        if actual == expected:
            self.log_success(f"{test_name}: {actual} == {expected}")
        else:
            self.log_error(f"{test_name}: 期望 {expected}, 实际 {actual}")
    
    def assert_not_none(self, value, test_name: str):
        """断言非空"""
        self.total += 1
        if value is not None and value != "":
            self.log_success(f"{test_name}: 值存在")
        else:
            self.log_error(f"{test_name}: 值为空")
    
    def assert_in_range(self, value, min_val, max_val, test_name: str):
        """断言在范围内"""
        self.total += 1
        if min_val <= value <= max_val:
            self.log_success(f"{test_name}: {value} 在范围 [{min_val}, {max_val}] 内")
        else:
            self.log_error(f"{test_name}: {value} 不在范围 [{min_val}, {max_val}] 内")
    
    def assert_greater_than(self, value, threshold, test_name: str):
        """断言大于"""
        self.total += 1
        if value > threshold:
            self.log_success(f"{test_name}: {value} > {threshold}")
        else:
            self.log_error(f"{test_name}: {value} <= {threshold}")
    
    def login(self) -> bool:
        """登录"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
                timeout=10
            )
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
        except Exception as e:
            self.log_error("登录失败", str(e))
        return False
    
    def test_dashboard_data_consistency(self):
        """测试Dashboard数据一致性"""
        print("\n" + "="*70)
        self.log_info("测试1: Dashboard数据一致性验证")
        print("="*70)
        
        try:
            # 获取Dashboard汇总数据
            dashboard = requests.get(
                f"{API_BASE}/dashboard/summary",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            # 获取产品列表
            products = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 1000},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            # 获取管理人列表
            managers = requests.get(
                f"{API_BASE}/managers",
                params={"skip": 0, "limit": 1000},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            # 验证产品数量一致性
            dashboard_product_count = dashboard.get("product_stats", {}).get("total", 0)
            actual_product_count = products.get("total", 0)
            self.assert_equal(
                dashboard_product_count, 
                actual_product_count,
                "Dashboard产品数量与实际产品数量一致"
            )
            
            # 验证管理人数量一致性
            dashboard_manager_count = dashboard.get("manager_stats", {}).get("total", 0)
            actual_manager_count = managers.get("total", 0)
            self.assert_equal(
                dashboard_manager_count,
                actual_manager_count,
                "Dashboard管理人数量与实际管理人数量一致"
            )
            
            self.log_info(f"Dashboard显示: {dashboard_product_count}个产品, {dashboard_manager_count}个管理人")
            self.log_info(f"实际数据: {actual_product_count}个产品, {actual_manager_count}个管理人")
            
            # 验证项目数量一致性
            dashboard_project_count = dashboard.get("project_stats", {}).get("total", 0)
            self.log_info(f"Dashboard显示: {dashboard_project_count}个项目")
            
            # 验证任务统计
            task_stats = dashboard.get("task_stats", {})
            self.log_info(f"任务统计: 总计{task_stats.get('total', 0)}个, 待办{task_stats.get('pending', 0)}个, 进行中{task_stats.get('in_progress', 0)}个, 已完成{task_stats.get('completed', 0)}个")
            
            # 验证任务数量加总逻辑
            total_calculated = task_stats.get('pending', 0) + task_stats.get('in_progress', 0) + task_stats.get('completed', 0)
            total_reported = task_stats.get('total', 0)
            self.assert_equal(
                total_calculated,
                total_reported,
                "任务各状态数量之和等于总数"
            )
            
        except Exception as e:
            self.log_error("Dashboard数据一致性测试失败", str(e))
    
    def test_product_data_integrity(self):
        """测试产品数据完整性"""
        print("\n" + "="*70)
        self.log_info("测试2: 产品数据完整性验证")
        print("="*70)
        
        try:
            # 获取产品列表
            response = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            products = response.json()
            items = products.get("items", [])
            
            if not items:
                self.log_warning("没有产品数据，跳过测试")
                return
            
            # 测试第一个产品
            product = items[0]
            product_id = product.get("id")
            
            self.log_info(f"测试产品: {product.get('product_name', 'N/A')} (ID: {product_id})")
            
            # 验证必填字段
            self.assert_not_none(product.get("product_name"), "产品名称不为空")
            self.assert_not_none(product.get("product_code"), "产品代码不为空")
            self.assert_not_none(product.get("manager_id"), "管理人ID不为空")
            
            # 验证产品详情
            detail = requests.get(
                f"{API_BASE}/products/{product_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            # 验证列表和详情数据一致
            self.assert_equal(
                product.get("product_name"),
                detail.get("product_name"),
                "产品列表和详情的产品名称一致"
            )
            
            self.assert_equal(
                product.get("product_code"),
                detail.get("product_code"),
                "产品列表和详情的产品代码一致"
            )
            
            # 验证管理人关联
            manager_id = product.get("manager_id")
            if manager_id:
                manager = requests.get(
                    f"{API_BASE}/managers/{manager_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                if manager.status_code == 200:
                    self.log_success(f"产品关联的管理人存在 (ID: {manager_id})")
                    self.total += 1
                    self.passed += 1
                else:
                    self.log_error(f"产品关联的管理人不存在 (ID: {manager_id})")
                    self.total += 1
                    self.failed += 1
            
        except Exception as e:
            self.log_error("产品数据完整性测试失败", str(e))
    
    def test_nav_data_accuracy(self):
        """测试净值数据准确性"""
        print("\n" + "="*70)
        self.log_info("测试3: 净值数据准确性验证")
        print("="*70)
        
        try:
            # 获取第一个产品
            products = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 1},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            if not products.get("items"):
                self.log_warning("没有产品数据，跳过测试")
                return
            
            product_id = products["items"][0]["id"]
            product_name = products["items"][0]["product_name"]
            
            self.log_info(f"测试产品净值: {product_name} (ID: {product_id})")
            
            # 获取净值数据
            nav_response = requests.get(
                f"{API_BASE}/nav",
                params={"product_id": product_id, "skip": 0, "limit": 100},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            nav_items = nav_response.get("items", [])
            
            if not nav_items:
                self.log_warning(f"产品 {product_id} 没有净值数据")
                return
            
            self.log_info(f"找到 {len(nav_items)} 条净值记录")
            
            # 验证净值数据合理性
            for i, nav in enumerate(nav_items[:5]):  # 只检查前5条
                nav_value = nav.get("nav")
                cumulative_nav = nav.get("cumulative_nav")
                nav_date = nav.get("nav_date")
                
                # 验证净值为正数
                if nav_value is not None:
                    self.assert_greater_than(
                        float(nav_value), 0,
                        f"第{i+1}条净值为正数 ({nav_date})"
                    )
                
                # 验证累计净值大于等于单位净值
                if nav_value and cumulative_nav:
                    self.total += 1
                    if float(cumulative_nav) >= float(nav_value):
                        self.log_success(f"第{i+1}条累计净值 >= 单位净值")
                    else:
                        self.log_error(f"第{i+1}条累计净值 < 单位净值")
                
                # 验证日期格式
                self.assert_not_none(nav_date, f"第{i+1}条净值日期不为空")
            
            # 验证净值按日期排序
            dates = [nav.get("nav_date") for nav in nav_items if nav.get("nav_date")]
            if len(dates) > 1:
                self.total += 1
                is_sorted = dates == sorted(dates, reverse=True)
                if is_sorted:
                    self.log_success("净值数据按日期倒序排列")
                else:
                    self.log_error("净值数据排序不正确")
            
        except Exception as e:
            self.log_error("净值数据准确性测试失败", str(e))
    
    def test_performance_calculation(self):
        """测试绩效计算准确性"""
        print("\n" + "="*70)
        self.log_info("测试4: 绩效计算准确性验证")
        print("="*70)
        
        try:
            # 获取第一个产品
            products = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 1},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            if not products.get("items"):
                self.log_warning("没有产品数据，跳过测试")
                return
            
            product_id = products["items"][0]["id"]
            product_name = products["items"][0]["product_name"]
            
            self.log_info(f"测试产品绩效: {product_name} (ID: {product_id})")
            
            # 获取绩效数据
            performance = requests.get(
                f"{API_BASE}/analysis/performance",
                params={"product_id": product_id},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if performance.status_code != 200:
                self.log_warning("绩效分析接口返回错误，可能产品无净值数据")
                return
            
            perf_data = performance.json()
            
            # 验证收益率在合理范围内 (-100% 到 1000%)
            if "total_return" in perf_data:
                total_return = perf_data["total_return"]
                self.assert_in_range(
                    total_return, -1.0, 10.0,
                    "累计收益率在合理范围内"
                )
            
            if "annualized_return" in perf_data:
                annual_return = perf_data["annualized_return"]
                self.assert_in_range(
                    annual_return, -1.0, 5.0,
                    "年化收益率在合理范围内"
                )
            
            # 验证波动率为正数
            if "volatility" in perf_data:
                volatility = perf_data["volatility"]
                if volatility is not None:
                    self.assert_greater_than(
                        volatility, 0,
                        "波动率为正数"
                    )
            
            # 验证最大回撤为负数或零
            if "max_drawdown" in perf_data:
                max_dd = perf_data["max_drawdown"]
                if max_dd is not None:
                    self.total += 1
                    if max_dd <= 0:
                        self.log_success(f"最大回撤 <= 0: {max_dd:.2%}")
                    else:
                        self.log_error(f"最大回撤应该 <= 0, 实际: {max_dd:.2%}")
            
            # 验证夏普比率在合理范围
            if "sharpe_ratio" in perf_data:
                sharpe = perf_data["sharpe_ratio"]
                if sharpe is not None:
                    self.assert_in_range(
                        sharpe, -5.0, 10.0,
                        "夏普比率在合理范围内"
                    )
            
        except Exception as e:
            self.log_error("绩效计算准确性测试失败", str(e))
    
    def test_task_workflow(self):
        """测试任务工作流"""
        print("\n" + "="*70)
        self.log_info("测试5: 任务工作流验证")
        print("="*70)
        
        try:
            # 获取任务列表
            tasks = requests.get(
                f"{API_BASE}/tasks",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            items = tasks.get("items", [])
            
            if not items:
                self.log_warning("没有任务数据，跳过测试")
                return
            
            self.log_info(f"找到 {len(items)} 个任务")
            
            # 验证任务状态合法性
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            for task in items:
                status = task.get("status")
                self.total += 1
                if status in valid_statuses:
                    self.log_success(f"任务状态合法: {status}")
                else:
                    self.log_error(f"任务状态非法: {status}")
            
            # 验证优先级合法性
            valid_priorities = ["low", "medium", "high", "urgent"]
            for task in items:
                priority = task.get("priority")
                if priority:
                    self.total += 1
                    if priority in valid_priorities:
                        self.log_success(f"任务优先级合法: {priority}")
                    else:
                        self.log_error(f"任务优先级非法: {priority}")
            
            # 验证截止日期逻辑
            for task in items:
                due_date = task.get("due_date")
                created_at = task.get("created_at")
                
                if due_date and created_at:
                    self.total += 1
                    if due_date >= created_at:
                        self.log_success("任务截止日期 >= 创建日期")
                    else:
                        self.log_error("任务截止日期 < 创建日期（逻辑错误）")
            
        except Exception as e:
            self.log_error("任务工作流测试失败", str(e))
    
    def test_project_cashflow_logic(self):
        """测试项目现金流逻辑"""
        print("\n" + "="*70)
        self.log_info("测试6: 项目现金流逻辑验证")
        print("="*70)
        
        try:
            # 获取项目列表
            projects = requests.get(
                f"{API_BASE}/projects",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            items = projects.get("items", [])
            
            if not items:
                self.log_warning("没有项目数据，跳过测试")
                return
            
            for project in items[:3]:  # 测试前3个项目
                project_id = project.get("id")
                project_name = project.get("project_name")
                
                self.log_info(f"测试项目: {project_name} (ID: {project_id})")
                
                # 获取项目详情
                detail = requests.get(
                    f"{API_BASE}/projects/{project_id}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                ).json()
                
                # 验证投资金额为正数
                investment_amount = detail.get("investment_amount")
                if investment_amount:
                    self.assert_greater_than(
                        float(investment_amount), 0,
                        f"项目 {project_name} 投资金额为正数"
                    )
                
                # 验证项目状态合法性
                valid_project_statuses = ["pending", "approved", "invested", "exited", "cancelled"]
                status = detail.get("status")
                if status:
                    self.total += 1
                    if status in valid_project_statuses:
                        self.log_success(f"项目 {project_name} 状态合法: {status}")
                    else:
                        self.log_error(f"项目 {project_name} 状态非法: {status}")
                
                # 验证投资日期逻辑
                investment_date = detail.get("investment_date")
                exit_date = detail.get("exit_date")
                
                if investment_date and exit_date:
                    self.total += 1
                    if exit_date >= investment_date:
                        self.log_success(f"项目 {project_name} 退出日期 >= 投资日期")
                    else:
                        self.log_error(f"项目 {project_name} 退出日期 < 投资日期（逻辑错误）")
            
        except Exception as e:
            self.log_error("项目现金流逻辑测试失败", str(e))
    
    def test_user_permission_logic(self):
        """测试用户权限逻辑"""
        print("\n" + "="*70)
        self.log_info("测试7: 用户权限逻辑验证")
        print("="*70)
        
        try:
            # 获取当前用户信息
            current_user = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            self.log_info(f"当前用户: {current_user.get('username')} ({current_user.get('real_name')})")
            self.log_info(f"用户角色: {current_user.get('role')}")
            
            # 验证用户角色合法性
            valid_roles = ["super_admin", "admin", "analyst", "viewer"]
            role = current_user.get("role")
            self.total += 1
            if role in valid_roles:
                self.log_success(f"用户角色合法: {role}")
            else:
                self.log_error(f"用户角色非法: {role}")
            
            # 验证用户状态
            valid_user_statuses = ["active", "inactive", "locked"]
            status = current_user.get("status")
            self.total += 1
            if status in valid_user_statuses:
                self.log_success(f"用户状态合法: {status}")
            else:
                self.log_error(f"用户状态非法: {status}")
            
            # 验证管理员权限
            if role == "super_admin":
                # 尝试访问用户管理接口
                users = requests.get(
                    f"{API_BASE}/users",
                    params={"skip": 0, "limit": 1},
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                self.total += 1
                if users.status_code == 200:
                    self.log_success("超级管理员可以访问用户管理接口")
                else:
                    self.log_error("超级管理员无法访问用户管理接口")
            
        except Exception as e:
            self.log_error("用户权限逻辑测试失败", str(e))
    
    def test_data_pagination(self):
        """测试数据分页逻辑"""
        print("\n" + "="*70)
        self.log_info("测试8: 数据分页逻辑验证")
        print("="*70)
        
        try:
            # 测试产品分页
            page1 = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            page2 = requests.get(
                f"{API_BASE}/products",
                params={"skip": 5, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            ).json()
            
            # 验证总数一致
            self.assert_equal(
                page1.get("total"),
                page2.get("total"),
                "不同页的总数一致"
            )
            
            # 验证返回数量
            items1 = page1.get("items", [])
            items2 = page2.get("items", [])
            
            self.total += 1
            if len(items1) <= 5:
                self.log_success(f"第1页返回数量正确: {len(items1)} <= 5")
            else:
                self.log_error(f"第1页返回数量错误: {len(items1)} > 5")
            
            # 验证两页数据不重复
            if items1 and items2:
                ids1 = {item["id"] for item in items1}
                ids2 = {item["id"] for item in items2}
                
                self.total += 1
                if ids1.isdisjoint(ids2):
                    self.log_success("不同页的数据不重复")
                else:
                    self.log_error("不同页的数据有重复")
            
        except Exception as e:
            self.log_error("数据分页逻辑测试失败", str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*70)
        print("🧪 FOF管理平台业务逻辑深度测试")
        print("="*70)
        print(f"服务器地址: {BACKEND_URL}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 登录
        self.log_info("正在登录...")
        if not self.login():
            self.log_error("登录失败，无法继续测试")
            return False
        self.log_success("登录成功")
        
        # 执行所有测试
        self.test_dashboard_data_consistency()
        self.test_product_data_integrity()
        self.test_nav_data_accuracy()
        self.test_performance_calculation()
        self.test_task_workflow()
        self.test_project_cashflow_logic()
        self.test_user_permission_logic()
        self.test_data_pagination()
        
        # 显示结果
        self.show_results()
        return self.failed == 0
    
    def show_results(self):
        """显示测试结果"""
        print("\n" + "="*70)
        self.log_info("📊 业务逻辑测试结果汇总")
        print("="*70)
        print()
        print(f"总测试数: {self.total}")
        print(f"{Colors.GREEN}通过: {self.passed}{Colors.NC}")
        print(f"{Colors.RED}失败: {self.failed}{Colors.NC}")
        
        if self.total > 0:
            success_rate = (self.passed / self.total) * 100
            print(f"通过率: {success_rate:.1f}%")
        
        print()
        
        if self.failed == 0:
            print(f"{Colors.GREEN}🎉 所有业务逻辑测试通过！{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ {self.failed} 个测试失败{Colors.NC}")
            print()
            print("失败的测试:")
            for result in self.test_results:
                if result[0] == "FAIL":
                    print(f"  ✗ {result[1]}")
                    if len(result) > 2:
                        print(f"    {result[2]}")
        print()

def main():
    tester = BusinessLogicTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
