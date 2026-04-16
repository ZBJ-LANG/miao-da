import sys
from pathlib import Path
import pymysql

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import config

def analyze_season_category():
    """分析每个季节每个品类的商品数量"""
    conn = pymysql.connect(
        host=config.MYSQL_HOST,
        port=config.MYSQL_PORT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # 统计每个季节每个品类的商品数量
            sql = """
            SELECT 
                season, 
                category, 
                COUNT(*) as count 
            FROM 
                products 
            GROUP BY 
                season, category 
            ORDER BY 
                season, category
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            print("=" * 60)
            print("每个季节每个品类的商品数量统计")
            print("=" * 60)
            print(f"{'季节':<10} {'品类':<10} {'数量':<10}")
            print("-" * 60)
            
            # 按季节分组显示
            current_season = None
            total_by_season = 0
            grand_total = 0
            
            for season, category, count in results:
                if season != current_season:
                    if current_season:
                        print(f"{'小计':<10} {'':<10} {total_by_season:<10}")
                        print("-" * 60)
                    current_season = season
                    total_by_season = 0
                print(f"{season:<10} {category:<10} {count:<10}")
                total_by_season += count
                grand_total += count
            
            # 打印最后一个季节的小计
            if current_season:
                print(f"{'小计':<10} {'':<10} {total_by_season:<10}")
                print("-" * 60)
            
            # 打印总计
            print(f"{'总计':<10} {'':<10} {grand_total:<10}")
            print("=" * 60)
            
            # 统计每个季节的商品数量
            print("\n每个季节的商品数量统计")
            print("=" * 40)
            print(f"{'季节':<10} {'数量':<10}")
            print("-" * 40)
            
            sql_season = """
            SELECT 
                season, 
                COUNT(*) as count 
            FROM 
                products 
            GROUP BY 
                season 
            ORDER BY 
                season
            """
            cursor.execute(sql_season)
            season_results = cursor.fetchall()
            
            for season, count in season_results:
                print(f"{season:<10} {count:<10}")
            
            print("-" * 40)
            print(f"{'总计':<10} {grand_total:<10}")
            print("=" * 40)
            
            # 统计每个品类的商品数量
            print("\n每个品类的商品数量统计")
            print("=" * 40)
            print(f"{'品类':<10} {'数量':<10}")
            print("-" * 40)
            
            sql_category = """
            SELECT 
                category, 
                COUNT(*) as count 
            FROM 
                products 
            GROUP BY 
                category 
            ORDER BY 
                count DESC
            """
            cursor.execute(sql_category)
            category_results = cursor.fetchall()
            
            for category, count in category_results:
                print(f"{category:<10} {count:<10}")
            
            print("-" * 40)
            print(f"{'总计':<10} {grand_total:<10}")
            print("=" * 40)
            
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始分析每个季节每个品类的商品数量...")
    analyze_season_category()
    print("分析完成!")
