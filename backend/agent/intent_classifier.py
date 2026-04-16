from typing import Literal
from pydantic import BaseModel


class IntentResult(BaseModel):
    intent: str
    confidence: float
    details: dict = {}


def classify_intent(message: str) -> IntentResult:
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['生成', '试穿', '虚拟', '效果图', '穿上', '生成图片']):
        return IntentResult(
            intent='virtual_tryon',
            confidence=0.9,
            details={'type': 'tryon'}
        )
    
    if any(word in message_lower for word in ['找', '搜索', '有没有', '想找', '想买', '想买', '看看', '帮我', '给我']):
        return IntentResult(
            intent='search',
            confidence=0.85,
            details={'type': 'search'}
        )
    
    if any(word in message_lower for word in ['搭配', '穿什么', '穿啥', '怎么搭', '推荐穿', '应该', '穿搭', '穿法']):
        return IntentResult(
            intent='recommendation',
            confidence=0.9,
            details={'type': 'recommendation'}
        )
    
    return IntentResult(
        intent='recommendation',
        confidence=0.5,
        details={'type': 'chat'}
    )


def extract_search_conditions(message: str) -> dict:
    conditions = {}
    message_lower = message.lower()
    
    # Extract category
    categories = {
        '衬衫': '上衣', 't恤': '上衣', 't恤': '上衣', '卫衣': '上衣', '毛衣': '上衣',
        '外套': '上衣', '大衣': '上衣', 'polo': '上衣', '背心': '上衣',
        '裤子': '下装', '短裤': '下装', '牛仔裤': '下装', '裙子': '下装', '休闲裤': '下装',
        '连衣裙': '连衣裙',
        '休闲鞋': '鞋子', '运动鞋': '鞋子', '帆布鞋': '鞋子', 
        '高跟鞋': '鞋子', '凉鞋': '鞋子', '靴子': '鞋子',
        '包包': '配件', '帽子': '配件', '围巾': '配件', '腰带': '配件'
    }
    
    for keyword, category in categories.items():
        if keyword in message_lower:
            conditions['category'] = category
            break
    
    # Extract color
    colors = [
        '白色', '黑色', '蓝色', '红色', '绿色', '黄色', '粉色', '紫色',
        '灰色', '棕色', '卡其色', '米色', '奶白色', '藏青色', '牛仔蓝'
    ]
    for color in colors:
        if color in message:
            conditions['color'] = color
            break
    
    # Extract style with enhanced keywords
    # Campus style
    campus_terms = ['校园', '学院', '学生', '校服', '学院风', '校园风', '学生装']
    for term in campus_terms:
        if term in message:
            conditions['style'] = '学院'
            break
    
    # Business style
    if 'style' not in conditions:
        business_terms = ['商务', '职场', '办公', '正装', '职业', '上班', '商务风', '职业装']
        for term in business_terms:
            if term in message:
                conditions['style'] = '商务'
                break
    
    # Casual style
    if 'style' not in conditions:
        casual_terms = ['休闲', '日常', '轻松', '休闲风', '日常装']
        for term in casual_terms:
            if term in message:
                conditions['style'] = '休闲'
                break
    
    # Sport style
    if 'style' not in conditions:
        sport_terms = ['运动', '健身', '跑步', '打球', '运动风', '健身装']
        for term in sport_terms:
            if term in message:
                conditions['style'] = '运动'
                break
    
    # Other styles
    if 'style' not in conditions:
        other_styles = {
            '复古': ['复古', '怀旧', ' vintage', '复古风'],
            '韩系': ['韩系', '韩国', '韩剧', '韩版', '韩风格'],
            '洛丽塔': ['洛丽塔', 'lolita', '萝莉塔'],
            '甜美': ['甜美', '可爱', '少女', '甜美风'],
            '性感': ['性感', '火辣', '夜店', '派对']
        }
        for style, terms in other_styles.items():
            for term in terms:
                if term in message:
                    conditions['style'] = style
                    break
            if 'style' in conditions:
                break
    
    # Extract season
    seasons = ['春天', '春季', '夏天', '夏季', '秋天', '秋季', '冬天', '冬季']
    for season in seasons:
        if season in message:
            if '春' in season:
                conditions['season'] = '春季'
            elif '夏' in season:
                conditions['season'] = '夏季'
            elif '秋' in season:
                conditions['season'] = '秋季'
            elif '冬' in season:
                conditions['season'] = '冬季'
            break
    
    # Extract occasion with enhanced keywords
    occasions = {
        '商务': ['商务', '职场', '办公', '会议', '出差'],
        '约会': ['约会', '约会装', '约会穿搭'],
        '日常': ['日常', '平时', '平常'],
        '聚会': ['聚会', '派对', '聚会装', '派对装'],
        '运动': ['运动', '健身', '跑步', '打球'],
        '婚礼': ['婚礼', '婚宴', '婚礼嘉宾'],
        '旅游': ['旅游', '旅行', '度假', '出游', '五一', '十一', '假期', '游玩'],
        '面试': ['面试', '面试装', '求职']
    }
    
    for occasion, terms in occasions.items():
        for term in terms:
            if term in message:
                conditions['occasion'] = occasion
                break
        if 'occasion' in conditions:
            break
    
    return conditions
