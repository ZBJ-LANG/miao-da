import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.database import init_db, get_db
from sqlalchemy import text

# 初始化数据库
init_db()

# 检查数据库连接
db = next(get_db())
try:
    # 执行简单的SQL查询
    result = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
    print('商品总数:', result)
    
    # 查看前5个商品
    print('前5个商品:')
    products = db.execute(text("SELECT id, name, price, category FROM products LIMIT 5")).fetchall()
    for p in products:
        print('ID:', p[0], '名称:', p[1], '价格:', p[2], '类别:', p[3])
finally:
    db.close()