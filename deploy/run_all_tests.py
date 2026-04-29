#!/usr/bin/env python3
"""
FOF管理平台综合测试套件
包含功能测试、性能测试和健康检查
"""

import subprocess
import sys
import os
from datetime import datetime

class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'

def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")

def run_test(script_name: str, description: str) -> bool:
    """运行测试脚本"""
    print("\n" + "="*70)
    log_info(f"{description}")
    print("="*70)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            log_success(f"{description} - 通过")
            return True
        else:
            log_error(f"{description} - 失败")
            return False
    except Exception as e:
        log_error(f"{description} - 执行异常: {e}")
        return False

def main():
    print("="*70)
    print("🧪 FOF管理平台综合测试套件")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()
    
    # 检查测试脚本是否存在
    test_scripts = [
        ("test_business.py", "业务功能测试"),
        ("test_performance.py", "性能压力测试"),
    ]
    
    missing_scripts = []
    for script, _ in test_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        log_error("以下测试脚本不存在:")
        for script in missing_scripts:
            print(f"  - {script}")
        sys.exit(1)
    
    # 运行测试
    results = []
    
    for script, description in test_scripts:
        success = run_test(script, description)
        results.append((description, success))
    
    # 汇总结果
    print("\n" + "="*70)
    log_info("📊 测试结果汇总")
    print("="*70)
    print()
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = f"{Colors.GREEN}✓ 通过{Colors.NC}" if success else f"{Colors.RED}✗ 失败{Colors.NC}"
        print(f"  {description}: {status}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    print()
    
    if passed == total:
        log_success("🎉 所有测试通过！")
        sys.exit(0)
    else:
        log_error("❌ 部分测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
