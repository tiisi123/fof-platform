#!/usr/bin/env python3
"""
FOF管理平台远程服务器业务功能测试
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# 配置 - 修改为你的服务器地址
SERVER_IP = "47.116.187.192"  # 从.env中看到的服务器IP
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

class RemoteTestRunner:
    def __init__(self):
        self.token = None
        self.passed = 0
        self.failed = 0
        self.total = 0
        
    def log_info(self, msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    def log_success(self, msg: str):
        print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")
        self.passed += 1
    
    def log_error(self, msg: str, detail: str = ""):
        print(f"{Colors.RED}[✗]{Colors.NC} {msg}")
        if detail:
            print(f"  详情: {detail}")
        self.failed += 1
    
    def log_warning(self, msg: str):
        print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")
    
    def test_connection(self) -> bool:
        """测试服务器连接"""
        self.total += 1
        self.log_info("测试服务器连接...")
        
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_success(f"服务器连接成功: {BACKEND_URL}")
                return True
            else:
                self.log_error(f"服务器响应异常 (状态码: {response.status_code})")
                return False
        except requests.exceptions.ConnectionError:
            self.log_error("无法连接到服务器", f"请检查: 1) 服务器是否运行 2) 端口{BACKEND_PORT}是否开放 3) IP地址是否正确")
            return False
        except Exception as e:
            self.log_error("连接测试失败", str(e))
            return False
    
    def test_login(self) -> bool:
        """测试登录"""
        self.total += 1
        self.log_info("测试管理员登录...")
        
        try:
            # 使用表单数据而不是JSON
            response = requests.post(
                f"{API_BASE}/auth/login",
                data={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.log_success("管理员登录成功")
                    return True
                else:
                    self.log_error("登录响应中未找到token")
                    return False
            else:
                self.log_error(f"登录失败 (状态码: {response.status_code})", response.text[:200])
                return False
        except Exception as e:
            self.log_error("登录请求异常", str(e))
            return False
    
    def test_dashboard(self):
        """测试Dashboard"""
        self.total += 1
        self.log_info("测试Dashboard数据...")
        
        try:
            response = requests.get(
                f"{API_BASE}/dashboard/summary",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success("Dashboard数据获取成功")
                self.log_info(f"  总规模: {data.get('total_aum', 0):.2f} 亿元")
                self.log_info(f"  产品数: {data.get('product_count', 0)} 个")
                self.log_info(f"  管理人: {data.get('manager_count', 0)} 个")
            else:
                self.log_error(f"Dashboard获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("Dashboard请求异常", str(e))
    
    def test_products(self):
        """测试产品管理"""
        self.total += 1
        self.log_info("测试产品列表...")
        
        try:
            response = requests.get(
                f"{API_BASE}/products",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                items = data.get("items", [])
                self.log_success(f"产品列表获取成功 (共 {total} 个产品)")
                if items:
                    self.log_info(f"  示例产品: {items[0].get('product_name', 'N/A')}")
            else:
                self.log_error(f"产品列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("产品列表请求异常", str(e))
    
    def test_managers(self):
        """测试管理人"""
        self.total += 1
        self.log_info("测试管理人列表...")
        
        try:
            response = requests.get(
                f"{API_BASE}/managers",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"管理人列表获取成功 (共 {total} 个)")
            else:
                self.log_error(f"管理人列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("管理人列表请求异常", str(e))
    
    def test_tasks(self):
        """测试待办任务"""
        self.total += 1
        self.log_info("测试待办任务...")
        
        try:
            response = requests.get(
                f"{API_BASE}/tasks",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"待办任务获取成功 (共 {total} 个)")
            else:
                self.log_error(f"待办任务获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("待办任务请求异常", str(e))
    
    def test_nav(self):
        """测试净值数据"""
        self.total += 1
        self.log_info("测试净值数据...")
        
        try:
            response = requests.get(
                f"{API_BASE}/nav",
                params={"product_id": 1, "skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"净值数据获取成功 (共 {total} 条)")
            else:
                self.log_error(f"净值数据获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("净值数据请求异常", str(e))
    
    def test_projects(self):
        """测试项目管理"""
        self.total += 1
        self.log_info("测试项目列表...")
        
        try:
            response = requests.get(
                f"{API_BASE}/projects",
                params={"skip": 0, "limit": 5},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                self.log_success(f"项目列表获取成功 (共 {total} 个)")
            else:
                self.log_error(f"项目列表获取失败 (状态码: {response.status_code})")
        except Exception as e:
            self.log_error("项目列表请求异常", str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*70)
        print("🧪 FOF管理平台远程服务器业务测试")
        print("="*70)
        print(f"服务器地址: {BACKEND_URL}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        print()
        
        # 1. 测试连接
        if not self.test_connection():
            self.log_error("服务器连接失败，无法继续测试")
            self.show_results()
            return False
        
        print()
        
        # 2. 测试登录
        if not self.test_login():
            self.log_error("登录失败，无法继续测试")
            self.show_results()
            return False
        
        print()
        
        # 3. 测试各个模块
        print("="*70)
        self.log_info("开始测试业务模块...")
        print("="*70)
        print()
        
        self.test_dashboard()
        print()
        
        self.test_products()
        print()
        
        self.test_managers()
        print()
        
        self.test_tasks()
        print()
        
        self.test_nav()
        print()
        
        self.test_projects()
        print()
        
        # 显示结果
        self.show_results()
        return self.failed == 0
    
    def show_results(self):
        """显示测试结果"""
        print("="*70)
        self.log_info("📊 测试结果汇总")
        print("="*70)
        print()
        print(f"总测试数: {self.total}")
        print(f"{Colors.GREEN}通过: {self.passed}{Colors.NC}")
        print(f"{Colors.RED}失败: {self.failed}{Colors.NC}")
        print()
        
        if self.failed == 0:
            print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ {self.failed} 个测试失败{Colors.NC}")
        print()

def main():
    print()
    print("提示: 如果服务器地址不是 47.116.187.192，请修改脚本中的 SERVER_IP 变量")
    print()
    
    runner = RemoteTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
