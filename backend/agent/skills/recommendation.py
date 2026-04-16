from typing import List, Optional
from models.product import Product, ProductSearch
from services.product_service import ProductService


def search_products_by_conditions(conditions: dict, limit: int = 20) -> List[Product]:
    service = ProductService()
    try:
        search = ProductSearch(
            category=conditions.get('category'),
            color=conditions.get('color'),
            style=conditions.get('style'),
            season=conditions.get('season'),
            keyword=conditions.get('keyword'),
            limit=limit
        )
        return service.search_products(search)
    finally:
        service.close()


def get_complementary_products(base_product: Product, limit: int = 5) -> List[Product]:
    service = ProductService()
    try:
        conditions = {}
        if base_product.category:
            opposite_categories = {
                '上衣': ['下装', '裤子', '裙子'],
                '下装': ['上衣', '鞋子'],
                '鞋子': ['上衣'],
                '配件': ['上衣', '下装']
            }
            cats = opposite_categories.get(base_product.category, [])
            conditions['category'] = cats[0] if cats else None
        
        if base_product.style:
            conditions['style'] = base_product.style
        
        search = ProductSearch(
            category=conditions.get('category'),
            style=conditions.get('style'),
            limit=limit
        )
        return service.search_products(search)
    finally:
        service.close()


def generate_outfit_from_products(top_products: List[Product], style: str = '休闲', user_profile: dict = None) -> dict:
    outfit_items = []
    
    # Get user profile information
    gender = user_profile.get('gender', '') if user_profile else ''
    body_type = user_profile.get('body_type', '') if user_profile else ''
    age = user_profile.get('age', 0) if user_profile else 0
    skin_tone = user_profile.get('skin_tone', '') if user_profile else ''
    
    # Filter products based on user profile
    filtered_products = top_products
    
    # Filter products based on gender
    if gender:
        # For female users, prefer female-specific products
        if gender == '女':
            gender_filtered = [p for p in filtered_products if '女' in p.name or '女士' in p.name or '女性' in p.name or '女款' in p.name or 'unisex' in p.name.lower()]
            if gender_filtered:
                filtered_products = gender_filtered
        # For male users, prefer male-specific products
        elif gender == '男':
            gender_filtered = [p for p in filtered_products if '男' in p.name or '男士' in p.name or '男性' in p.name or '男款' in p.name or 'unisex' in p.name.lower()]
            if gender_filtered:
                filtered_products = gender_filtered
    
    # Filter products based on body type
    if body_type:
        if body_type == '苗条':
            # For slim body type, prefer fitted clothes
            body_filtered = [p for p in filtered_products if '修身' in p.name or '紧身' in p.name or '苗条' in p.name or '显瘦' in p.name]
            if body_filtered:
                filtered_products = body_filtered
        elif body_type == '丰满':
            # For curvy body type, prefer loose-fitting clothes
            body_filtered = [p for p in filtered_products if '宽松' in p.name or '休闲' in p.name or '舒适' in p.name or '遮肉' in p.name]
            if body_filtered:
                filtered_products = body_filtered
    
    # Filter products based on age
    if age:
        if age < 20:
            # For younger users, prefer trendy clothes
            age_filtered = [p for p in filtered_products if '潮流' in p.name or '时尚' in p.name or '青春' in p.name or '学生' in p.name]
            if age_filtered:
                filtered_products = age_filtered
        elif age > 50:
            # For older users, prefer classic clothes
            age_filtered = [p for p in filtered_products if '经典' in p.name or '稳重' in p.name or '成熟' in p.name or '优雅' in p.name]
            if age_filtered:
                filtered_products = age_filtered
    
    # Filter products based on skin tone
    if skin_tone:
        if skin_tone == '白皙':
            # For fair skin, prefer bright colors
            skin_filtered = [p for p in filtered_products if '白色' in p.name or '粉色' in p.name or '蓝色' in p.name or '浅' in p.name]
            if skin_filtered:
                filtered_products = skin_filtered
        elif skin_tone == '小麦色':
            # For wheat skin, prefer warm colors
            skin_filtered = [p for p in filtered_products if '黄色' in p.name or '橙色' in p.name or '棕色' in p.name or '暖' in p.name]
            if skin_filtered:
                filtered_products = skin_filtered
        elif skin_tone == '古铜色':
            # For bronze skin, prefer dark colors
            skin_filtered = [p for p in filtered_products if '黑色' in p.name or '深蓝色' in p.name or '深' in p.name]
            if skin_filtered:
                filtered_products = skin_filtered
    
    # Get different categories of products
    tops = [p for p in filtered_products if p.category in ['上衣']]
    bottoms = [p for p in filtered_products if p.category in ['下装', '裤子', '裙子']]
    shoes = [p for p in filtered_products if p.category == '鞋子']
    accessories = [p for p in filtered_products if p.category == '配件']
    dresses = [p for p in filtered_products if p.category == '连衣裙']
    
    # If no products found after filtering, use original products
    if not (tops or bottoms or shoes or accessories or dresses):
        print("DEBUG: No products found after filtering, using original products")
        tops = [p for p in top_products if p.category in ['上衣']]
        bottoms = [p for p in top_products if p.category in ['下装', '裤子', '裙子']]
        shoes = [p for p in top_products if p.category == '鞋子']
        accessories = [p for p in top_products if p.category == '配件']
        dresses = [p for p in top_products if p.category == '连衣裙']
    
    # If not enough categories, search from '四季' season
    if not (tops or bottoms or dresses) or not shoes:
        print("DEBUG: Not enough categories, searching from '四季' season")
        service = ProductService()
        try:
            # Search for missing categories from '四季' season
            if not tops:
                season_search = ProductSearch(
                    category='上衣',
                    season='四季',
                    style=style,
                    limit=10
                )
                season_products = service.search_products(season_search)
                if season_products:
                    tops = season_products
                    print("DEBUG: Added tops from '四季' season")
            
            if not bottoms:
                season_search = ProductSearch(
                    category='下装',
                    season='四季',
                    style=style,
                    limit=10
                )
                season_products = service.search_products(season_search)
                if season_products:
                    bottoms = season_products
                    print("DEBUG: Added bottoms from '四季' season")
            
            if not dresses:
                season_search = ProductSearch(
                    category='连衣裙',
                    season='四季',
                    style=style,
                    limit=10
                )
                season_products = service.search_products(season_search)
                if season_products:
                    dresses = season_products
                    print("DEBUG: Added dresses from '四季' season")
            
            if not shoes:
                season_search = ProductSearch(
                    category='鞋子',
                    season='四季',
                    style=style,
                    limit=10
                )
                season_products = service.search_products(season_search)
                if season_products:
                    shoes = season_products
                    print("DEBUG: Added shoes from '四季' season")
            
            if not accessories:
                season_search = ProductSearch(
                    category='配件',
                    season='四季',
                    style=style,
                    limit=10
                )
                season_products = service.search_products(season_search)
                if season_products:
                    accessories = season_products
                    print("DEBUG: Added accessories from '四季' season")
        finally:
            service.close()
    
    # Build outfit: either (top + bottom + shoes) or (dress + shoes)
    outfit_built = False
    
    # Option 1: Top + Bottom + Shoes
    if tops and bottoms and shoes:
        outfit_items.append({
            'type': '上衣',
            'product': tops[0],
            'sort_order': 1
        })
        
        # For different body types, choose different styles
        if body_type == '苗条':
            # For slim body type, choose fitted bottoms
            fitted_bottoms = [p for p in bottoms if '修身' in p.name or '紧身' in p.name or '苗条' in p.name]
            if fitted_bottoms:
                outfit_items.append({
                    'type': '下装',
                    'product': fitted_bottoms[0],
                    'sort_order': 2
                })
            else:
                outfit_items.append({
                    'type': '下装',
                    'product': bottoms[0],
                    'sort_order': 2
                })
        elif body_type == '丰满':
            # For curvy body type, choose A-line or loose-fitting bottoms
            loose_bottoms = [p for p in bottoms if '宽松' in p.name or '休闲' in p.name or 'A字' in p.name]
            if loose_bottoms:
                outfit_items.append({
                    'type': '下装',
                    'product': loose_bottoms[0],
                    'sort_order': 2
                })
            else:
                outfit_items.append({
                    'type': '下装',
                    'product': bottoms[0],
                    'sort_order': 2
                })
        else:
            outfit_items.append({
                'type': '下装',
                'product': bottoms[0],
                'sort_order': 2
            })
        
        outfit_items.append({
            'type': '鞋子',
            'product': shoes[0],
            'sort_order': 3
        })
        
        outfit_built = True
    
    # Option 2: Dress + Shoes
    elif dresses and shoes:
        outfit_items.append({
            'type': '连衣裙',
            'product': dresses[0],
            'sort_order': 1
        })
        
        outfit_items.append({
            'type': '鞋子',
            'product': shoes[0],
            'sort_order': 2
        })
        
        outfit_built = True
    
    # Option 3: At least one of top/bottom + shoes
    elif (tops or bottoms) and shoes:
        if tops:
            outfit_items.append({
                'type': '上衣',
                'product': tops[0],
                'sort_order': 1
            })
        if bottoms:
            outfit_items.append({
                'type': '下装',
                'product': bottoms[0],
                'sort_order': 2
            })
        outfit_items.append({
            'type': '鞋子',
            'product': shoes[0],
            'sort_order': 3
        })
        outfit_built = True
    
    # Add accessories based on style
    if accessories and style:
        # Filter accessories that match the style
        style_accessories = [a for a in accessories if style in a.name or style in (a.style or '')]
        if style_accessories:
            outfit_items.append({
                'type': '配件',
                'product': style_accessories[0],
                'sort_order': len(outfit_items) + 1
            })
        else:
            # Add any accessory if no style-specific ones found
            outfit_items.append({
                'type': '配件',
                'product': accessories[0],
                'sort_order': len(outfit_items) + 1
            })
    
    # If still no outfit built, create a basic outfit with available items
    if not outfit_built:
        print("DEBUG: Building basic outfit with available items")
        if tops:
            outfit_items.append({
                'type': '上衣',
                'product': tops[0],
                'sort_order': 1
            })
        if bottoms:
            outfit_items.append({
                'type': '下装',
                'product': bottoms[0],
                'sort_order': 2
            })
        if dresses:
            outfit_items.append({
                'type': '连衣裙',
                'product': dresses[0],
                'sort_order': 1
            })
        if shoes:
            outfit_items.append({
                'type': '鞋子',
                'product': shoes[0],
                'sort_order': len(outfit_items) + 1
            })
    
    # Sort items by sort_order
    outfit_items.sort(key=lambda x: x['sort_order'])
    
    return {
        'outfit_name': f'{style}搭配',
        'items': outfit_items,
        'total_price': sum(item['product'].price or 0 for item in outfit_items)
    }
