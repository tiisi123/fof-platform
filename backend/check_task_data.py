"""检查任务和用户数据"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.models.task import Task
from app.models.user import User
from app.models.product import Product
from app.models.manager import Manager
from app.models.portfolio import Portfolio

db = SessionLocal()

# 检查用户
users = db.query(User).all()
print(f'用户数: {len(users)}')
for u in users:
    print(f'  用户ID={u.id}, 用户名={u.username}, 真实姓名={u.real_name}, 角色={u.role}')

# 检查任务
tasks = db.query(Task).all()
print(f'\n当前任务数: {len(tasks)}')
for t in tasks:
    print(f'  任务ID={t.id}, 标题={t.title}, 状态={t.status}, 优先级={t.priority}')

# 检查其他数据
products = db.query(Product).count()
managers = db.query(Manager).count()
portfolios = db.query(Portfolio).count()

print(f'\n产品数: {products}')
print(f'管理人数: {managers}')
print(f'组合数: {portfolios}')

db.close()
