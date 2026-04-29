#!/usr/bin/env python3
"""
FOF管理平台性能测试脚本
测试API响应时间和并发性能
"""

import requests
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict

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

class PerformanceTest:
    def __init__(self):
        self.token = None
        self.results = {}
        
    def log_info(self, msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")
    
    def log_success(self, msg: str):
        print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")
    
    def log_error(self, msg: str):
        print(f"{Colors.RED}[✗]{Colors.NC} {msg}")
    
    def log_warning(self, msg: str):
        print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")
    
    def login(self) -> bool:
        """登录获取Token"""
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD},
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True
        except Exception as e:
            self.log_error(f"登录失败: {e}")
        return False
    
    def measure_response_time(self, endpoint: str, method: str = "GET", 
                             params: Dict = None, data: Dict = None) -> float:
        """测量单次请求响应时间"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{API_BASE}{endpoint}"
        
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                return elapsed
            else:
                return -1
        except Exception as e:
            return -1
    
    def test_endpoint_performance(self, name: str, endpoint: str, 
                                  iterations: int = 10) -> Dict:
        """测试单个端点的性能"""
        self.log_info(f"测试 {name} (执行 {iterations} 次)...")
        
        times = []
        failures = 0
        
        for i in range(iterations):
            elapsed = self.measure_response_time(endpoint)
            if elapsed > 0:
                times.append(elapsed)
            else:
                failures += 1
        
        if not times:
            self.log_error(f"{name}: 所有请求失败")
            return None
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "iterations": iterations,
            "failures": failures,
            "min": min(times) * 1000,  # 转换为毫秒
            "max": max(times) * 1000,
            "avg": statistics.mean(times) * 1000,
            "median": statistics.median(times) * 1000,
            "p95": statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else max(times) * 1000,
        }
        
        # 评估性能
        avg_ms = result["avg"]
        if avg_ms < 200:
            status = f"{Colors.GREEN}优秀{Colors.NC}"
        elif avg_ms < 500:
            status = f"{Colors.GREEN}良好{Colors.NC}"
        elif avg_ms < 1000:
            status = f"{Colors.YELLOW}一般{Colors.NC}"
        else:
            status = f"{Colors.RED}较慢{Colors.NC}"
        
        self.log_success(
            f"{name}: 平均 {avg_ms:.0f}ms, "
            f"中位数 {result['median']:.0f}ms, "
            f"P95 {result['p95']:.0f}ms - {status}"
        )
        
        return result
    
    def test_concurrent_requests(self, endpoint: str, concurrent: int = 10) -> Dict:
        """测试并发请求性能"""
        self.log_info(f"测试并发性能 (并发数: {concurrent})...")
        
        def make_request():
            return self.measure_response_time(endpoint)
        
        start_time = time.time()
        times = []
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent)]
            
            for future in as_completed(futures):
                elapsed = future.result()
                if elapsed > 0:
                    times.append(elapsed)
        
        total_time = time.time() - start_time
        
        if not times:
            self.log_error("所有并发请求失败")
            return None
        
        result = {
            "concurrent": concurrent,
            "total_time": total_time,
            "successful": len(times),
            "failed": concurrent - len(times),
            "avg_response": statistics.mean(times) * 1000,
            "requests_per_second": len(times) / total_time,
        }
        
        self.log_success(
            f"并发测试完成: {result['successful']}/{concurrent} 成功, "
            f"平均响应 {result['avg_response']:.0f}ms, "
            f"吞吐量 {result['requests_per_second']:.1f} req/s"
        )
        
        return result
    
    def run_performance_tests(self):
        """运行所有性能测试"""
        print("="*60)
        print("🚀 FOF管理平台性能测试")
        print("="*60)
        print(f"后端地址: {BACKEND_URL}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print()
        
        # 登录
        self.log_info("正在登录...")
        if not self.login():
            self.log_error("登录失败，无法继续测试")
            return
        self.log_success("登录成功")
        print()
        
        # 定义测试端点
        endpoints = [
            ("健康检查", "/health", "GET"),
            ("Dashboard摘要", "/dashboard/summary", "GET"),
            ("产品列表", "/products/?skip=0&limit=10", "GET"),
            ("管理人列表", "/managers/?skip=0&limit=10", "GET"),
            ("净值数据", "/nav/?product_id=1&skip=0&limit=10", "GET"),
            ("任务列表", "/tasks/?skip=0&limit=10", "GET"),
            ("用户列表", "/users/?skip=0&limit=10", "GET"),
        ]
        
        # 响应时间测试
        print("="*60)
        self.log_info("1. 响应时间测试")
        print("="*60)
        print()
        
        results = []
        for name, endpoint, method in endpoints:
            # 跳过健康检查的认证
            if endpoint == "/health":
                result = self.test_endpoint_performance_no_auth(name, endpoint)
            else:
                result = self.test_endpoint_performance(name, endpoint)
            
            if result:
                results.append(result)
            time.sleep(0.5)  # 避免过快请求
        
        print()
        
        # 并发测试
        print("="*60)
        self.log_info("2. 并发性能测试")
        print("="*60)
        print()
        
        concurrent_tests = [
            ("低并发", "/dashboard/summary", 5),
            ("中并发", "/dashboard/summary", 10),
            ("高并发", "/dashboard/summary", 20),
        ]
        
        concurrent_results = []
        for name, endpoint, concurrent in concurrent_tests:
            result = self.test_concurrent_requests(endpoint, concurrent)
            if result:
                result["name"] = name
                concurrent_results.append(result)
            time.sleep(1)
        
        print()
        
        # 生成报告
        self.generate_report(results, concurrent_results)
    
    def test_endpoint_performance_no_auth(self, name: str, endpoint: str, 
                                         iterations: int = 10) -> Dict:
        """测试不需要认证的端点"""
        self.log_info(f"测试 {name} (执行 {iterations} 次)...")
        
        times = []
        failures = 0
        url = f"{BACKEND_URL}{endpoint}"
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(url, timeout=30)
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    times.append(elapsed)
                else:
                    failures += 1
            except:
                failures += 1
        
        if not times:
            self.log_error(f"{name}: 所有请求失败")
            return None
        
        result = {
            "name": name,
            "endpoint": endpoint,
            "iterations": iterations,
            "failures": failures,
            "min": min(times) * 1000,
            "max": max(times) * 1000,
            "avg": statistics.mean(times) * 1000,
            "median": statistics.median(times) * 1000,
            "p95": statistics.quantiles(times, n=20)[18] * 1000 if len(times) >= 20 else max(times) * 1000,
        }
        
        avg_ms = result["avg"]
        if avg_ms < 200:
            status = f"{Colors.GREEN}优秀{Colors.NC}"
        elif avg_ms < 500:
            status = f"{Colors.GREEN}良好{Colors.NC}"
        elif avg_ms < 1000:
            status = f"{Colors.YELLOW}一般{Colors.NC}"
        else:
            status = f"{Colors.RED}较慢{Colors.NC}"
        
        self.log_success(
            f"{name}: 平均 {avg_ms:.0f}ms, "
            f"中位数 {result['median']:.0f}ms, "
            f"P95 {result['p95']:.0f}ms - {status}"
        )
        
        return result
    
    def generate_report(self, results: List[Dict], concurrent_results: List[Dict]):
        """生成性能测试报告"""
        print("="*60)
        self.log_info("📊 性能测试报告")
        print("="*60)
        print()
        
        # 响应时间汇总
        print("响应时间汇总:")
        print("-" * 60)
        print(f"{'端点':<20} {'平均':<10} {'中位数':<10} {'P95':<10} {'状态':<10}")
        print("-" * 60)
        
        for result in results:
            avg = result['avg']
            if avg < 200:
                status = "优秀"
            elif avg < 500:
                status = "良好"
            elif avg < 1000:
                status = "一般"
            else:
                status = "较慢"
            
            print(f"{result['name']:<20} {avg:<10.0f} {result['median']:<10.0f} "
                  f"{result['p95']:<10.0f} {status:<10}")
        
        print()
        
        # 并发性能汇总
        if concurrent_results:
            print("并发性能汇总:")
            print("-" * 60)
            print(f"{'测试':<15} {'并发数':<10} {'成功率':<10} {'吞吐量(req/s)':<15}")
            print("-" * 60)
            
            for result in concurrent_results:
                success_rate = result['successful'] / result['concurrent'] * 100
                print(f"{result['name']:<15} {result['concurrent']:<10} "
                      f"{success_rate:<10.1f}% {result['requests_per_second']:<15.1f}")
            
            print()
        
        # 性能建议
        print("性能建议:")
        print("-" * 60)
        
        slow_endpoints = [r for r in results if r['avg'] > 1000]
        if slow_endpoints:
            self.log_warning("以下端点响应较慢，建议优化:")
            for r in slow_endpoints:
                print(f"  - {r['name']}: {r['avg']:.0f}ms")
        else:
            self.log_success("所有端点响应时间良好")
        
        print()
        
        # 保存JSON报告
        report = {
            "test_time": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "response_time_tests": results,
            "concurrent_tests": concurrent_results,
        }
        
        with open("performance_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log_info("详细报告已保存到: performance_report.json")

def main():
    tester = PerformanceTest()
    tester.run_performance_tests()

if __name__ == "__main__":
    main()
