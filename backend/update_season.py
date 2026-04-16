import re
import sys
from pathlib import Path
import pymysql

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

# 季节关键词映射
SEASON_KEYWORDS = {
    '春季': ['春', '春季', '春款', '春装', '浅色系', '轻薄'],
    '夏季': ['夏', '夏季', '夏款', '夏装', '短袖', '短裤', '凉鞋', '轻薄', '透气', '清爽'],
    '秋季': ['秋', '秋季', '秋款', '秋装', '长袖', '外套', '针织', '毛衣'],
    '冬季': ['冬', '冬季', '冬款', '冬装', '羽绒服', '棉服', '厚外套', '保暖', '加绒'],
    '四季': ['四季', '百搭', '通用', '经典', '基础']
}

# 分类季节映射
CATEGORY_SEASON_MAPPING = {
    'T恤': '夏季',
    '短袖': '夏季',
    '短裤': '夏季',
    '凉鞋': '夏季',
    '背心': '夏季',
    '衬衫': '四季',
    '卫衣': '春秋',
    '毛衣': '秋冬',
    '外套': '春秋',
    '大衣': '冬季',
    '羽绒服': '冬季',
    '棉服': '冬季',
    '牛仔裤': '四季',
    '休闲裤': '四季',
    '裙子': '春夏',
    '连衣裙': '春夏',
    '半身裙': '春夏',
    '休闲鞋': '四季',
    '运动鞋': '四季',
    '帆布鞋': '春夏',
    '高跟鞋': '四季',
    '靴子': '秋冬',
    '包包': '四季',
    '帽子': '四季',
    '围巾': '秋冬',
    '腰带': '四季',
    '袜子': '四季'
}

def determine_season(name, category, sub_category):
    """根据商品名称和分类确定季节"""
    name_lower = name.lower()
    
    # 首先检查名称中的季节关键词
    for season, keywords in SEASON_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return season
    
    # 然后根据子分类判断
    if sub_category:
        for category_key, season in CATEGORY_SEASON_MAPPING.items():
            if category_key in sub_category:
                return season
    
    # 最后根据主分类判断
    if category == '上衣':
        return '四季'
    elif category == '下装':
        return '四季'
    elif category == '鞋子':
        return '四季'
    elif category == '配件':
        return '四季'
    elif category == '连衣裙':
        return '春夏'
    
    return '四季'

def update_season_field():
    """更新数据库中所有商品的季节字段"""
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    try:
        # 获取所有商品
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, category, sub_category FROM products")
            products = cursor.fetchall()
        
        print(f"Found {len(products)} products to update")
        
        # 更新每个商品的季节字段
        updated_count = 0
        with conn.cursor() as cursor:
            for product in products:
                product_id, name, category, sub_category = product
                season = determine_season(name, category, sub_category)
                
                # 更新数据库
                update_sql = "UPDATE products SET season = %s WHERE id = %s"
                cursor.execute(update_sql, (season, product_id))
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"Updated {updated_count} products...")
        
        conn.commit()
        print(f"Successfully updated season field for {updated_count} products")
        
    except Exception as e:
        print(f"Error updating season field: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Updating season field for all products...")
    update_season_field()
    print("Season field update completed!")
