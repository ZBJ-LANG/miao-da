from services.database import ProductModel, SessionLocal

# 创建数据库会话
db = SessionLocal()

# 检查商品总数
total_count = db.query(ProductModel).count()
print(f"Total products: {total_count}")

# 检查休闲风格的商品
casual_count = db.query(ProductModel).filter(ProductModel.style == '休闲').count()
print(f"Casual style products: {casual_count}")

# 检查春夏季节的商品
spring_summer_count = db.query(ProductModel).filter(ProductModel.season == '春夏').count()
print(f"Spring/Summer products: {spring_summer_count}")

# 检查同时符合休闲风格和春夏季节的商品
casual_spring_summer_count = db.query(ProductModel).filter(
    ProductModel.style == '休闲',
    ProductModel.season == '春夏'
).count()
print(f"Casual style + Spring/Summer products: {casual_spring_summer_count}")

# 查看前5个商品的详细信息
sample_products = db.query(ProductModel).limit(5).all()
print("\nSample products:")
for i, product in enumerate(sample_products):
    print(f"Product {i+1}:")
    print(f"  Name: {product.name}")
    print(f"  Category: {product.category}")
    print(f"  Style: {product.style}")
    print(f"  Season: {product.season}")
    print(f"  Price: {product.price}")
    print()

# 关闭数据库会话
db.close()