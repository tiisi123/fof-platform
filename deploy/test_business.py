#!/usr/bin/env python3
"""
FOF管理平台业务功能测试脚本
测试所有核心业务模块的API接口，生成详细测试报告
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import time

# 配置
BACKEND_URL = "http://localhost:8506"
API_BASE = f"{BACKEND_URL}/api/v1"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

# 颜色代码
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

class TestRunner:
    def __init__(self):
        self.token = None
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        
    def log_info(self, msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    def log_success(self, msg: str):
        print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")
        self.passed_tests += 1
        self.results.append(("PASS", msg))
    
    def log_error(self, msg: str, detail: str = ""):
        print(f"{Colors.RED}[✗]{Colors.NC} {msg}")
        if detail:
            print(f"  详情: {detail}")
        self.failed_tests += 1
        self.results.append(("FAIL", msg, detail))
    
    def log_warning(self, msg: str):
        print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")
    
    def test_start(self):
        self.total_tests += 1
    
    def check_service(self) -> bool:
        """检查服务状态"""
        self.log_info("检查后端服务状态...")
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log_success("后端服务运行正常")
                return True
        except Exception as e:
            self.log_error("后端服务无响应", str(e))
        return False
    
    def test_auth(self) -> bool:
        """用户认证测试"""
        print("\n" + "="*50)
        self.log_info("1. 用户认证模块测试")
        print("="*50)
        
        # 测试登录
        self.test_start()
        self.log_info("测试管理员登录...")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                if self.token:
                    self.log_success("管理员登录成功")
                    self.log_info(f"Token: {self.token[:20]}...")
                else:
                    self.log_error("登录响应中未找到token")
                    return False
            else:
                self.log_error(f"登录失败 (状态码: {response.status_code})", response.text)
                return False
        except Exception as e:
            self.log_error("登录请求异常", str(e))
            return False
        
        # 测试获取当前用户信息
        self.test_start()
        self.log_info("测试获取当前用户信息...")
        
        try:
            response = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("username") == DEFAULT_USERNAME:
                    self.log_success(f"获取用户信息成功: {data.get('real_name', 'N/A')}")
                else:
                    self.log_error("用户信息不匹配")
            else:
                self.log_error(f"获取用户信息失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("获取用户信息异常", str(e))
        
        return True
    
    def test_dashboard(self):
        """Dashboard测试"""
        print("\n" + "="*50)
        self.log_info("2. Dashboard模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试Dashboard数据获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/dashboard/summary",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success("Dashboard数据获取成功")
                
                # 显示关键指标
                total_aum = data.get("total_aum", 0)
                product_count = data.get("product_count", 0)
                manager_count = data.get("manager_count", 0)
                
                self.log_info(f"  总规模: {total_aum:.2f} 亿元")
                self.log_info(f"  产品数量: {product_count} 个")
                self.log_info(f"  管理人数量: {manager_count} 个")
            else:
                self.log_error(f"Dashboard数据获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("Dashboard请求异常", str(e))
    
    def test_products(self):
        """产品管理测试"""
        print("\n" + "="*50)
        self.log_info("3. 产品管理模块测试")
        print("="*50)
        
        # 测试产品列表
        self.test_start()
        self.log_info("测试产品列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/products/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                total = data.get("total", 0)
                
                self.log_success(f"产品列表获取成功 (共 {total} 个产品)")
                
                if items:
                    # 测试第一个产品的详情
                    product_id = items[0].get("id")
                    self.test_product_detail(product_id)
            else:
                self.log_error(f"产品列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("产品列表请求异常", str(e))
    
    def test_product_detail(self, product_id: int):
        """测试产品详情"""
        self.test_start()
        self.log_info(f"测试产品详情获取 (ID: {product_id})...")
        
        try:
            response = requests.get(
                f"{API_BASE}/products/{product_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                product_name = data.get("product_name", "N/A")
                self.log_success(f"产品详情获取成功: {product_name}")
            else:
                self.log_error(f"产品详情获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("产品详情请求异常", str(e))
    
    def test_managers(self):
        """管理人测试"""
        print("\n" + "="*50)
        self.log_info("4. 管理人模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试管理人列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/managers/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"管理人列表获取成功 (共 {total} 个管理人)")
            else:
                self.log_error(f"管理人列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("管理人列表请求异常", str(e))
    
    def test_nav(self):
        """净值管理测试"""
        print("\n" + "="*50)
        self.log_info("5. 净值管理模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试净值数据获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/nav/",
                params={"product_id": 1, "skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"净值数据获取成功 (共 {total} 条记录)")
            else:
                self.log_error(f"净值数据获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("净值数据请求异常", str(e))
    
    def test_holdings(self):
        """持仓管理测试"""
        print("\n" + "="*50)
        self.log_info("6. 持仓管理模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试持仓数据获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/holdings/",
                params={"product_id": 1},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_success("持仓数据获取成功")
            else:
                self.log_error(f"持仓数据获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("持仓数据请求异常", str(e))
    
    def test_analysis(self):
        """绩效分析测试"""
        print("\n" + "="*50)
        self.log_info("7. 绩效分析模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试绩效指标计算...")
        
        try:
            response = requests.get(
                f"{API_BASE}/analysis/performance",
                params={"product_id": 1},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success("绩效指标计算成功")
                
                # 显示关键指标
                if "total_return" in data:
                    self.log_info(f"  累计收益率: {data.get('total_return', 0):.2%}")
                if "annualized_return" in data:
                    self.log_info(f"  年化收益率: {data.get('annualized_return', 0):.2%}")
            else:
                self.log_error(f"绩效指标计算失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("绩效分析请求异常", str(e))
    
    def test_attribution(self):
        """因子归因测试"""
        print("\n" + "="*50)
        self.log_info("8. 因子归因模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试因子归因分析...")
        
        try:
            response = requests.get(
                f"{API_BASE}/attribution/factor-analysis",
                params={"product_id": 1},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_success("因子归因分析成功")
            else:
                self.log_error(f"因子归因分析失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("因子归因请求异常", str(e))
    
    def test_projects(self):
        """项目管理测试"""
        print("\n" + "="*50)
        self.log_info("9. 项目管理模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试项目列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/projects/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"项目列表获取成功 (共 {total} 个项目)")
            else:
                self.log_error(f"项目列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("项目列表请求异常", str(e))
    
    def test_tasks(self):
        """待办任务测试"""
        print("\n" + "="*50)
        self.log_info("10. 待办任务模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试任务列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/tasks/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"任务列表获取成功 (共 {total} 个任务)")
            else:
                self.log_error(f"任务列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("任务列表请求异常", str(e))
    
    def test_documents(self):
        """文档管理测试"""
        print("\n" + "="*50)
        self.log_info("11. 文档管理模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试文档列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/documents/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"文档列表获取成功 (共 {total} 个文档)")
            else:
                self.log_error(f"文档列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("文档列表请求异常", str(e))
    
    def test_calendar(self):
        """日历事件测试"""
        print("\n" + "="*50)
        self.log_info("12. 日历事件模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试日历事件获取...")
        
        try:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            response = requests.get(
                f"{API_BASE}/calendar/events",
                params={"start_date": start_date, "end_date": end_date},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_success("日历事件获取成功")
            else:
                self.log_error(f"日历事件获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("日历事件请求异常", str(e))
    
    def test_audit(self):
        """审计日志测试"""
        print("\n" + "="*50)
        self.log_info("13. 审计日志模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试审计日志获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/audit/logs",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"审计日志获取成功 (共 {total} 条记录)")
            else:
                self.log_error(f"审计日志获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("审计日志请求异常", str(e))
    
    def test_users(self):
        """用户管理测试"""
        print("\n" + "="*50)
        self.log_info("14. 用户管理模块测试")
        print("="*50)
        
        self.test_start()
        self.log_info("测试用户列表获取...")
        
        try:
            response = requests.get(
                f"{API_BASE}/users/",
                params={"skip": 0, "limit": 10},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"用户列表获取成功 (共 {total} 个用户)")
            else:
                self.log_error(f"用户列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("用户列表请求异常", str(e))
    
    def show_results(self):
        """显示测试结果"""
        duration = time.time() - self.start_time
        
        print("\n" + "="*50)
        self.log_info("📊 测试结果汇总")
        print("="*50)
        print()
        print(f"总测试数: {self.total_tests}")
        print(f"{Colors.GREEN}通过: {self.passed_tests}{Colors.NC}")
        print(f"{Colors.RED}失败: {self.failed_tests}{Colors.NC}")
        print(f"耗时: {duration:.2f} 秒")
        print()
        
        if self.failed_tests == 0:
            print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.NC}")
            return True
        else:
            print(f"{Colors.RED}❌ 部分测试失败{Colors.NC}")
            print()
            print("失败的测试:")
            for result in self.results:
                if result[0] == "FAIL":
                    print(f"  ✗ {result[1]}")
                    if len(result) > 2 and result[2]:
                        print(f"    {result[2]}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*50)
        print("🧪 FOF管理平台业务功能测试")
        print("="*50)
        print(f"后端地址: {BACKEND_URL}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        print()
        
        self.start_time = time.time()
        
        # 检查服务
        if not self.check_service():
            self.log_error("服务未运行，请先启动服务")
            return False
        
        # 执行测试
        if not self.test_auth():
            self.log_error("认证失败，无法继续测试")
            return False
        
        self.test_dashboard()
        self.test_products()
        self.test_managers()
        self.test_nav()
        self.test_holdings()
        self.test_analysis()
        self.test_attribution()
        self.test_projects()
        self.test_tasks()
        self.test_documents()
        self.test_calendar()
        self.test_audit()
        self.test_users()
        
        # 显示结果
        return self.show_results()

def main():
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
