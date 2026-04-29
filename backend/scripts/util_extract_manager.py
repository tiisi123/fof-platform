"""
从基金名称中智能提取管理人名称
"""
import re
from typing import Optional


def extract_manager_name(fund_name: str) -> Optional[str]:
    """
    从基金名称中提取管理人名称
    
    规则:
    1. 如果包含"信托-"，提取信托后面的部分
    2. 如果是"XX私募证券投资基金"，提取XX部分
    3. 如果是"XX证券投资基金"，提取XX部分
    4. 提取前面的关键词
    
    示例:
    - "外贸信托-睿郡稳享尊享B期集合资金信托计划" -> "睿郡"
    - "远澜红枫1号私募证券投资基金" -> "远澜"
    - "宽远优势成长2号证券投资基金" -> "宽远"
    - "东源嘉盈2号证券投资基金" -> "东源"
    """
    if not fund_name:
        return None
    
    # 规则1: 信托产品
    if "信托-" in fund_name:
        # 提取信托后面的部分
        parts = fund_name.split("信托-")
        if len(parts) > 1:
            after_trust = parts[1]
            # 提取第一个中文词
            match = re.match(r'([^\d\s]+)', after_trust)
            if match:
                return match.group(1)
    
    # 规则2: 标准私募基金名称
    # 匹配: XX私募证券投资基金, XX证券投资基金, XX期货基金
    patterns = [
        r'^([^\d\s]{2,6})[\d\w]*(?:私募)?(?:证券投资|期货|股权投资)?基金',
        r'^([^\d\s]{2,6})[\d\w]*(?:号|期)',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, fund_name)
        if match:
            manager_name = match.group(1)
            # 过滤掉一些常见的非管理人词汇
            exclude_words = ['外贸', '中信', '华润', '平安', '招商', '兴业', '光大']
            if manager_name not in exclude_words:
                return manager_name
    
    # 规则3: 提取前2-4个汉字
    match = re.match(r'^([^\d\s]{2,4})', fund_name)
    if match:
        return match.group(1)
    
    return None


# 测试
if __name__ == "__main__":
    test_cases = [
        "外贸信托-睿郡稳享尊享B期集合资金信托计划",
        "远澜红枫1号私募证券投资基金",
        "远澜云杉期货基金",
        "宽远优势成长2号证券投资基金",
        "东源嘉盈2号证券投资基金",
        "明河清源5号私募证券投资基金",
        "骏骁稳健1号私募证券投资基金",
    ]
    
    print("=" * 70)
    print("测试管理人名称提取")
    print("=" * 70)
    
    for fund_name in test_cases:
        manager_name = extract_manager_name(fund_name)
        print(f"{fund_name}")
        print(f"  -> {manager_name}")
        print()
