"""
重新生成待办任务数据
基于实际的产品、管理人、组合数据生成真实的任务
"""
import sys
import os
# 添加backend目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from datetime import datetime, timedelta, date
import random
from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.product import Product
from app.models.manager import Manager
from app.models.portfolio import Portfolio

def main():
    db = SessionLocal()
    
    try:
        # 获取用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            print("错误: 未找到admin用户")
            return
        
        print(f"找到用户: {admin_user.username} (ID={admin_user.id})")
        
        # 删除旧任务
        old_count = db.query(Task).count()
        db.query(Task).delete()
        db.commit()
        print(f"已删除 {old_count} 个旧任务")
        
        # 获取数据
        products = db.query(Product).all()
        managers = db.query(Manager).all()
        portfolios = db.query(Portfolio).all()
        
        print(f"\n数据统计:")
        print(f"  产品数: {len(products)}")
        print(f"  管理人数: {len(managers)}")
        print(f"  组合数: {len(portfolios)}")
        
        # 生成任务
        tasks = []
        today = date.today()
        
        # 1. 管理人相关任务 (10个)
        print("\n生成管理人相关任务...")
        manager_tasks = [
            ("完成{manager}尽调报告", TaskPriority.URGENT, -2, TaskStatus.PENDING),
            ("准备{manager}投决会材料", TaskPriority.URGENT, 1, TaskStatus.PENDING),
            ("跟进{manager}季度路演", TaskPriority.HIGH, 3, TaskStatus.PENDING),
            ("更新{manager}运营数据", TaskPriority.HIGH, 5, TaskStatus.IN_PROGRESS),
            ("审核{manager}投资协议", TaskPriority.MEDIUM, 7, TaskStatus.PENDING),
            ("联系{manager}产品对接", TaskPriority.MEDIUM, 10, TaskStatus.PENDING),
            ("整理{manager}历史业绩", TaskPriority.MEDIUM, 15, TaskStatus.PENDING),
            ("安排{manager}实地访谈", TaskPriority.LOW, 20, TaskStatus.PENDING),
            ("跟踪{manager}合规情况", TaskPriority.HIGH, -5, TaskStatus.COMPLETED),
            ("完成{manager}年度评估", TaskPriority.MEDIUM, -10, TaskStatus.COMPLETED),
        ]
        
        selected_managers = random.sample(managers, min(10, len(managers)))
        for i, (title_template, priority, days_offset, status) in enumerate(manager_tasks):
            if i < len(selected_managers):
                manager = selected_managers[i]
                title = title_template.format(manager=manager.manager_name)
                due_date = today + timedelta(days=days_offset)
                
                task = Task(
                    title=title,
                    description=f"针对{manager.manager_name}的{title.split(manager.manager_name)[1]}工作",
                    status=status,
                    priority=priority,
                    manager_id=manager.id,
                    assigned_to=admin_user.id,
                    created_by=admin_user.id,
                    due_date=due_date,
                    completed_at=datetime.now() - timedelta(days=abs(days_offset)) if status == TaskStatus.COMPLETED else None,
                )
                tasks.append(task)
        
        # 2. 产品相关任务 (15个)
        print("生成产品相关任务...")
        product_tasks = [
            ("更新{product}净值数据", TaskPriority.HIGH, 0, TaskStatus.PENDING),
            ("跟踪{product}业绩表现", TaskPriority.HIGH, 1, TaskStatus.PENDING),
            ("分析{product}回撤原因", TaskPriority.URGENT, 2, TaskStatus.IN_PROGRESS),
            ("准备{product}月度报告", TaskPriority.MEDIUM, 3, TaskStatus.PENDING),
            ("审核{product}持仓变化", TaskPriority.MEDIUM, 5, TaskStatus.PENDING),
            ("评估{product}风险指标", TaskPriority.HIGH, 7, TaskStatus.PENDING),
            ("对比{product}同类产品", TaskPriority.LOW, 10, TaskStatus.PENDING),
            ("整理{product}历史数据", TaskPriority.LOW, 15, TaskStatus.PENDING),
            ("跟进{product}申赎情况", TaskPriority.MEDIUM, 20, TaskStatus.PENDING),
            ("完成{product}归因分析", TaskPriority.HIGH, -3, TaskStatus.COMPLETED),
            ("更新{product}估值数据", TaskPriority.MEDIUM, -5, TaskStatus.COMPLETED),
            ("审核{product}费用结算", TaskPriority.MEDIUM, -7, TaskStatus.COMPLETED),
            ("准备{product}季度总结", TaskPriority.HIGH, -15, TaskStatus.COMPLETED),
            ("分析{product}风格漂移", TaskPriority.MEDIUM, -20, TaskStatus.COMPLETED),
            ("评估{product}投资价值", TaskPriority.LOW, -30, TaskStatus.COMPLETED),
        ]
        
        selected_products = random.sample(products, min(15, len(products)))
        for i, (title_template, priority, days_offset, status) in enumerate(product_tasks):
            if i < len(selected_products):
                product = selected_products[i]
                title = title_template.format(product=product.product_name[:20])
                due_date = today + timedelta(days=days_offset)
                
                task = Task(
                    title=title,
                    description=f"针对{product.product_name}的{title.split(product.product_name[:20])[1] if product.product_name[:20] in title else '相关'}工作",
                    status=status,
                    priority=priority,
                    product_id=product.id,
                    assigned_to=admin_user.id,
                    created_by=admin_user.id,
                    due_date=due_date,
                    completed_at=datetime.now() - timedelta(days=abs(days_offset)) if status == TaskStatus.COMPLETED else None,
                )
                tasks.append(task)
        
        # 3. 组合相关任务 (8个)
        print("生成组合相关任务...")
        portfolio_tasks = [
            ("调整{portfolio}资产配置", TaskPriority.URGENT, 1, TaskStatus.PENDING),
            ("优化{portfolio}持仓结构", TaskPriority.HIGH, 3, TaskStatus.IN_PROGRESS),
            ("评估{portfolio}风险敞口", TaskPriority.HIGH, 5, TaskStatus.PENDING),
            ("准备{portfolio}投资报告", TaskPriority.MEDIUM, 7, TaskStatus.PENDING),
            ("分析{portfolio}业绩归因", TaskPriority.MEDIUM, 10, TaskStatus.PENDING),
            ("更新{portfolio}估值数据", TaskPriority.HIGH, -2, TaskStatus.COMPLETED),
            ("完成{portfolio}季度总结", TaskPriority.MEDIUM, -10, TaskStatus.COMPLETED),
            ("审核{portfolio}调仓方案", TaskPriority.HIGH, -15, TaskStatus.COMPLETED),
        ]
        
        for i, (title_template, priority, days_offset, status) in enumerate(portfolio_tasks):
            if i < len(portfolios):
                portfolio = portfolios[i]
                title = title_template.format(portfolio=portfolio.name)
                due_date = today + timedelta(days=days_offset)
                
                task = Task(
                    title=title,
                    description=f"针对{portfolio.name}组合的{title.split(portfolio.name)[1]}工作",
                    status=status,
                    priority=priority,
                    portfolio_id=portfolio.id,
                    assigned_to=admin_user.id,
                    created_by=admin_user.id,
                    due_date=due_date,
                    completed_at=datetime.now() - timedelta(days=abs(days_offset)) if status == TaskStatus.COMPLETED else None,
                )
                tasks.append(task)
        
        # 4. 通用任务 (7个)
        print("生成通用任务...")
        general_tasks = [
            ("准备月度投资总结报告", TaskPriority.HIGH, 2, TaskStatus.PENDING, "汇总本月投资情况，准备月度报告"),
            ("更新管理人数据库信息", TaskPriority.MEDIUM, 5, TaskStatus.PENDING, "更新所有管理人的最新运营数据"),
            ("整理季度投资策略报告", TaskPriority.HIGH, 7, TaskStatus.IN_PROGRESS, "准备下季度投资策略和配置建议"),
            ("跟进待投项目进展", TaskPriority.MEDIUM, 10, TaskStatus.PENDING, "跟踪所有待投项目的最新进展"),
            ("审核投资协议条款", TaskPriority.HIGH, 15, TaskStatus.PENDING, "审核新签投资协议的关键条款"),
            ("完成年度尽调计划", TaskPriority.MEDIUM, -5, TaskStatus.COMPLETED, "完成本年度管理人尽调计划"),
            ("整理投资数据归档", TaskPriority.LOW, -10, TaskStatus.COMPLETED, "整理和归档历史投资数据"),
        ]
        
        for title, priority, days_offset, status, description in general_tasks:
            due_date = today + timedelta(days=days_offset)
            
            task = Task(
                title=title,
                description=description,
                status=status,
                priority=priority,
                assigned_to=admin_user.id,
                created_by=admin_user.id,
                due_date=due_date,
                completed_at=datetime.now() - timedelta(days=abs(days_offset)) if status == TaskStatus.COMPLETED else None,
            )
            tasks.append(task)
        
        # 批量插入
        db.bulk_save_objects(tasks)
        db.commit()
        
        print(f"\n任务生成完成!")
        print(f"  总任务数: {len(tasks)}")
        print(f"  待处理: {sum(1 for t in tasks if t.status == TaskStatus.PENDING)}")
        print(f"  进行中: {sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)}")
        print(f"  已完成: {sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)}")
        print(f"  紧急: {sum(1 for t in tasks if t.priority == TaskPriority.URGENT)}")
        print(f"  高优先级: {sum(1 for t in tasks if t.priority == TaskPriority.HIGH)}")
        print(f"  中优先级: {sum(1 for t in tasks if t.priority == TaskPriority.MEDIUM)}")
        print(f"  低优先级: {sum(1 for t in tasks if t.priority == TaskPriority.LOW)}")
        
        # 统计逾期任务
        overdue = sum(1 for t in tasks if t.due_date and t.due_date < today and t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        print(f"  逾期任务: {overdue}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
