"""
测试组合净值对比API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests

# API基础URL
BASE_URL = "http://localhost:8506/api/v1"

def get_token():
    """获取测试token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("登录失败")
        sys.exit(1)

def test_nav_compare(token, period):
    """测试组合净值对比API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n测试周期: {period}")
    print("="*60)
    
    response = requests.get(
        f"{BASE_URL}/dashboard/portfolio-nav-compare",
        headers=headers,
        params={"period": period}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"组合数量: {len(data.get('portfolios', []))}")
        print(f"净值序列: {len(data.get('nav_series', {}))}")
        print(f"绩效指标: {len(data.get('performance', {}))}")
        
        # 打印第一个组合的数据点数量
        if data.get('nav_series'):
            first_pf = list(data['nav_series'].values())[0]
            print(f"第一个组合数据点: {len(first_pf.get('dates', []))}")
            print(f"日期范围: {first_pf.get('dates', ['无'])[0]} ~ {first_pf.get('dates', ['无'])[-1]}")
    else:
        print(f"错误: {response.text}")

def main():
    print("="*60)
    print("测试组合净值对比API")
    print("="*60)
    
    token = get_token()
    print("✅ 登录成功\n")
    
    # 测试不同周期
    for period in ['3m', '6m', '1y', 'inception']:
        test_nav_compare(token, period)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
