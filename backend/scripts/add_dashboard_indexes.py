"""
添加Dashboard性能优化索引

优化总览页面的查询性能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def add_indexes():
    """添加性能优化索引"""
    
    indexes = [
        # 管理人表索引
        "CREATE INDEX IF NOT EXISTS idx_manager_pool ON managers(pool_category) WHERE is_deleted = 0",
        "CREATE INDEX IF NOT EXISTS idx_manager_strategy ON managers(primary_strategy) WHERE is_deleted = 0",
        "CREATE INDEX IF NOT EXISTS idx_manager_deleted ON managers(is_deleted)",
        
        # 产品表索引
        "CREATE INDEX IF NOT EXISTS idx_product_status ON products(status)",
        "CREATE INDEX IF NOT EXISTS idx_product_manager ON products(manager_id)",
        "CREATE INDEX IF NOT EXISTS idx_product_strategy ON products(strategy_type)",
        
        # 净值数据表索引（复合索引）
        "CREATE INDEX IF NOT EXISTS idx_nav_product_date ON nav_data(product_id, nav_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_nav_date ON nav_data(nav_date DESC)",
        
        # 组合表索引
        "CREATE INDEX IF NOT EXISTS idx_portfolio_type ON portfolios(portfolio_type)",
        "CREATE INDEX IF NOT EXISTS idx_portfolio_status ON portfolios(status)",
        
        # 组合净值表索引
        "CREATE INDEX IF NOT EXISTS idx_portfolio_nav_date ON portfolio_nav(portfolio_id, nav_date DESC)",
        
        # 组合持仓表索引
        "CREATE INDEX IF NOT EXISTS idx_portfolio_holdings ON portfolio_holdings(portfolio_id, holding_date DESC)",
        
        # 项目表索引
        "CREATE INDEX IF NOT EXISTS idx_project_stage ON projects(stage)",
        "CREATE INDEX IF NOT EXISTS idx_project_industry ON projects(industry)",
        
        # 任务表索引
        "CREATE INDEX IF NOT EXISTS idx_task_assignee ON tasks(assignee_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_task_due_date ON tasks(due_date)",
    ]
    
    print("=" * 60)
    print("添加Dashboard性能优化索引")
    print("=" * 60)
    print()
    
    with engine.connect() as conn:
        for i, sql in enumerate(indexes, 1):
            try:
                print(f"[{i}/{len(indexes)}] 执行: {sql[:80]}...")
                conn.execute(text(sql))
                conn.commit()
                print(f"✅ 成功")
            except Exception as e:
                print(f"❌ 失败: {e}")
            print()
    
    print("=" * 60)
    print("索引添加完成！")
    print("=" * 60)
    print()
    print("优化效果：")
    print("- 管理人统计查询：预计提升 50-70%")
    print("- 产品统计查询：预计提升 40-60%")
    print("- 净值数据查询：预计提升 60-80%")
    print("- 组合净值查询：预计提升 70-90%")
    print()

if __name__ == "__main__":
    add_indexes()
