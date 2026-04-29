"""
查看待办任务统计信息
"""
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from datetime import date
from app.core.database import SessionLocal
from app.models.task import Task, TaskStatus, TaskPriority

def main():
    db = SessionLocal()
    
    try:
        tasks = db.query(Task).all()
        today = date.today()
        
        print("=" * 60)
        print("待办任务统计")
        print("=" * 60)
        
        print(f"\n总任务数: {len(tasks)}")
        
        # 按状态统计
        print("\n按状态分类:")
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        
        print(f"  待处理: {len(pending)}")
        print(f"  进行中: {len(in_progress)}")
        print(f"  已完成: {len(completed)}")
        
        # 按优先级统计
        print("\n按优先级分类:")
        urgent = [t for t in tasks if t.priority == TaskPriority.URGENT]
        high = [t for t in tasks if t.priority == TaskPriority.HIGH]
        medium = [t for t in tasks if t.priority == TaskPriority.MEDIUM]
        low = [t for t in tasks if t.priority == TaskPriority.LOW]
        
        print(f"  紧急: {len(urgent)}")
        print(f"  高优先级: {len(high)}")
        print(f"  中优先级: {len(medium)}")
        print(f"  低优先级: {len(low)}")
        
        # 按关联对象统计
        print("\n按关联对象分类:")
        with_product = [t for t in tasks if t.product_id]
        with_manager = [t for t in tasks if t.manager_id]
        with_portfolio = [t for t in tasks if t.portfolio_id]
        general = [t for t in tasks if not t.product_id and not t.manager_id and not t.portfolio_id]
        
        print(f"  关联产品: {len(with_product)}")
        print(f"  关联管理人: {len(with_manager)}")
        print(f"  关联组合: {len(with_portfolio)}")
        print(f"  通用任务: {len(general)}")
        
        # 逾期任务
        overdue = [t for t in tasks if t.due_date and t.due_date < today and t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
        print(f"\n逾期任务: {len(overdue)}")
        if overdue:
            for t in overdue:
                print(f"  - {t.title} (截止: {t.due_date})")
        
        # 近期任务
        upcoming = [t for t in tasks if t.due_date and today <= t.due_date <= today + timedelta(days=7) and t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
        print(f"\n近7天到期任务: {len(upcoming)}")
        if upcoming:
            for t in sorted(upcoming, key=lambda x: x.due_date):
                print(f"  - {t.title} (截止: {t.due_date})")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    from datetime import timedelta
    main()
