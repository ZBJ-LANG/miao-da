import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.database import get_db
from models.product import Product

db = next(get_db())
try:
    print('商品总数:', db.query(Product).count())
    print('前5个商品:')
    for p in db.query(Product).limit(5).all():
        print('ID:', p.id, '名称:', p.name, '价格:', p.price, '类别:', p.category)
finally:
    db.close()