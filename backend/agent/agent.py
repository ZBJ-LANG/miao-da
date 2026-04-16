from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
import asyncio

from agent.intent_classifier import classify_intent, extract_search_conditions
from agent.skills.recommendation import search_products_by_conditions, generate_outfit_from_products
from agent.skills.search import search_products
from agent.tools.weather import get_weather, get_weather_suggestion
from agent.llm_service import classify_intent_with_llm, generate_recommendation_reason, map_style_to_db, llm_service


class AgentState(TypedDict):
    message: str
    user_id: str
    session_id: str
    intent: str
    conditions: dict
    products: list
    outfit: dict
    response: dict
    user_profile: dict


def intent_node(state: AgentState) -> AgentState:
    result = classify_intent(state['message'])
    state['intent'] = result
    return state


async def intent_node_llm(state: AgentState) -> AgentState:
    # Skip LLM classification for now to avoid encoding issues
    message = state['message']
    print(f"DEBUG: Using rule-based classifier directly for message: {message}")
    print(f"DEBUG: Message repr: {repr(message)}")
    print(f"DEBUG: Message length: {len(message)}")
    
    # Check if message is garbled (contains only ? characters)
    if all(c == '?' for c in message):
        print("DEBUG: Detected garbled message, using default recommendation intent")
        from agent.intent_classifier import IntentResult
        state['intent'] = IntentResult(
            intent='recommendation',
            confidence=0.9,
            details={'type': 'recommendation'}
        )
        state['conditions'] = {}
        # Set a default style for garbled messages
        state['conditions']['style'] = '休闲'
        print("DEBUG: Set default style to '休闲' for garbled message")
    else:
        result = classify_intent(message)
        state['intent'] = result
        state['conditions'] = {}
    
    return state


def extract_conditions_node(state: AgentState) -> AgentState:
    intent_obj = state['intent']
    if hasattr(intent_obj, 'details') and intent_obj.details.get('conditions'):
        for key, value in intent_obj.details['conditions'].items():
            if key not in state['conditions']:
                state['conditions'][key] = value
    else:
        message = state['message']
        conditions = extract_search_conditions(message)
        print(f"DEBUG: Extracted conditions: {conditions}")
        for key, value in conditions.items():
            if key not in state['conditions']:
                state['conditions'][key] = value
        
        # Special handling for common scene requests
        # Even if message is garbled, try to detect common patterns
        message_lower = message.lower()
        
        # Check if message is garbled (contains only ? characters)
        if all(c == '?' for c in message):
            print("DEBUG: Detected garbled message, trying to infer style from common patterns")
            # For garbled messages, we'll try to infer the intent based on common patterns
            # This is a fallback for when encoding issues prevent proper message parsing
            # In a production environment, you would want to fix the encoding issue at the source
            
            # Common travel-related patterns
            # Since we can't read the actual message, we'll use a heuristic based on common requests
            # For example, if the user is asking about travel outfits, we'll set style
            state['conditions']['style'] = '休闲'
            print("DEBUG: Set default travel-related conditions for garbled message")
        else:
            # Campus-related requests
            campus_terms = ['校园', '学院', '学生', '校服', '学院风', '校园风', '学生装', 'school', 'campus']
            for term in campus_terms:
                if term in message_lower:
                    state['conditions']['style'] = '学院'
                    print("DEBUG: Detected campus-related message, setting style to '学院'")
                    break
            
            # Business-related requests
            if 'style' not in state['conditions']:
                business_terms = ['商务', '职场', '办公', '正装', '职业', '上班', '商务风', '职业装', 'office', 'business']
                for term in business_terms:
                    if term in message_lower:
                        state['conditions']['style'] = '商务'
                        print("DEBUG: Detected business-related message, setting style to '商务'")
                        break
            
            # Sport-related requests
            if 'style' not in state['conditions']:
                sport_terms = ['运动', '健身', '跑步', '打球', '运动风', '健身装', 'sport', 'fitness']
                for term in sport_terms:
                    if term in message_lower:
                        state['conditions']['style'] = '运动'
                        print("DEBUG: Detected sport-related message, setting style to '运动'")
                        break
            
            # Casual-related requests
            if 'style' not in state['conditions']:
                casual_terms = ['休闲', '日常', '轻松', '休闲风', '日常装', 'casual', 'daily']
                for term in casual_terms:
                    if term in message_lower:
                        state['conditions']['style'] = '休闲'
                        print("DEBUG: Detected casual-related message, setting style to '休闲'")
                        break
    
    # Map occasion to style if no style is specified
    if 'style' not in state['conditions'] and 'occasion' in state['conditions']:
        occasion_to_style = {
            '商务': '商务',
            '面试': '商务',
            '约会': '甜美',
            '聚会': '性感',
            '运动': '运动',
            '旅游': '休闲',
            '婚礼': '正式'
        }
        occasion = state['conditions']['occasion']
        if occasion in occasion_to_style:
            state['conditions']['style'] = occasion_to_style[occasion]
            print(f"DEBUG: Mapped occasion '{occasion}' to style '{occasion_to_style[occasion]}'")
    
    # Only set default style if not already extracted
    if 'style' not in state['conditions']:
        state['conditions']['style'] = '休闲'
        print("DEBUG: Using '休闲' style as default")
    
    # Remove fields that are not supported by product search
    if 'occasion' in state['conditions']:
        del state['conditions']['occasion']
    # Keep season field for product search
    # if 'season' in state['conditions']:
    #     del state['conditions']['season']
    
    print(f"DEBUG: Before map_style_to_db: {state['conditions']}")
    if 'style' in state['conditions']:
        state['conditions']['style'] = map_style_to_db(state['conditions']['style'])
    print(f"DEBUG: After map_style_to_db: {state['conditions']}")
    
    return state


def search_node(state: AgentState) -> AgentState:
    conditions = state['conditions']
    print(f"DEBUG: Searching with conditions: {conditions}")
    products = search_products_by_conditions(conditions, limit=20)
    print(f"DEBUG: Found {len(products)} products")
    state['products'] = [
        {
            'name': p.name,
            'price': p.price or 0,
            'image_url': p.image_url or '',
            'product_url': p.product_url or '',
            'category': p.category,
            'color': p.color,
            'style': p.style
        }
        for p in products
    ]
    return state


def recommend_node(state: AgentState) -> AgentState:
    print(f"DEBUG: Recommending with conditions: {state['conditions']}")
    print(f"DEBUG: User profile: {state['user_profile']}")
    
    # Get gender from user profile to filter products
    gender = state['user_profile'].get('gender', '')
    print(f"DEBUG: User gender: {gender}")
    
    products = search_products_by_conditions(state['conditions'], limit=30)
    print(f"DEBUG: Found {len(products)} products for recommendation")
    
    # Generate outfit with user profile consideration
    state['outfit'] = generate_outfit_from_products(
        products,
        style=state['conditions'].get('style', '休闲'),
        user_profile=state['user_profile']
    )
    print(f"DEBUG: Generated outfit with {len(state['outfit']['items'])} items")
    return state


async def generate_outfit_image(items: list, style: str, user_profile: dict = None) -> str:
    """生成虚拟试穿图"""
    print("DEBUG: Starting generate_outfit_image")
    if not items or len(items) == 0:
        print("DEBUG: No items provided")
        return None
    
    # 提取商品信息
    item_descriptions = []
    detailed_item_descriptions = []
    product_image_urls = []
    
    # 提取商品信息和图片URL
    for i, item in enumerate(items[:3]):  # 只使用前3个商品
        name = item.get('name', '')
        image_url = item.get('image_url', '')
        color = item.get('color', '')
        category = item.get('category', '')
        
        item_descriptions.append(name)
        
        # 构建详细的商品描述，包含颜色、类别等信息
        detailed_desc = name
        if color:
            detailed_desc += f"（{color}色）"
        if category:
            detailed_desc += f"，{category}"
        
        detailed_item_descriptions.append(detailed_desc)
        
        # 收集有效的商品图片URL
        if image_url and (image_url.startswith('http://') or image_url.startswith('https://')):
            product_image_urls.append(image_url)
        
        print(f"DEBUG: Extracted item: {name}")
        print(f"DEBUG: Item color: {color}")
        print(f"DEBUG: Item category: {category}")
        print(f"DEBUG: Item image URL: {image_url}")
    
    # 选择第一个商品图片作为基础图片
    base_image_url = None
    if product_image_urls:
        base_image_url = product_image_urls[0]
        print(f"DEBUG: Selected product base image: {base_image_url}")
    else:
        # 如果没有商品图片，使用默认图片
        base_image_url = "https://img.alicdn.com/imgextra/i4/1924119553/O1CN01N7qEst2KRKD6zfMVz_!!1924119553.jpg"
        print(f"DEBUG: No product images found, using default base image: {base_image_url}")
    
    # 构建用户信息
    user_info = ""
    if user_profile:
        gender = user_profile.get('gender', '女性')
        age = user_profile.get('age', 25)
        body_type = user_profile.get('body_type', '标准')
        user_info = f"{gender}，{age}岁，{body_type}身材"
    else:
        # 默认使用女性模特
        user_info = "女性，25岁，标准身材"
    
    # 构建详细的提示词
    prompt = f"时尚穿搭，{style}风格，{user_info}模特，穿着以下服装：{', '.join(detailed_item_descriptions)}，模特姿态自然，背景简洁，高质量，真实感，清晰细节，光线自然，专业摄影效果"
    print(f"DEBUG: Generated prompt: {prompt}")
    
    try:
        # 从商品图片中提取特征
        product_features = []
        if product_image_urls:
            for i, img_url in enumerate(product_image_urls[:3]):  # 最多分析3张图片
                print(f"DEBUG: Analyzing product image {i+1}: {img_url}")
                try:
                    # 分析图片，提取特征
                    analysis = await llm_service.vision_chat(img_url)
                    if analysis:
                        print(f"DEBUG: Image analysis result: {analysis}")
                        # 解析分析结果
                        import json
                        try:
                            result = json.loads(analysis)
                            features = []
                            if result.get('style'):
                                features.append(f"风格：{result['style']}")
                            if result.get('color'):
                                features.append(f"颜色：{result['color']}")
                            if result.get('category'):
                                features.append(f"类别：{result['category']}")
                            if result.get('description'):
                                features.append(f"描述：{result['description']}")
                            if features:
                                product_features.append(f"商品{i+1}特征：{', '.join(features)}")
                        except json.JSONDecodeError:
                            print(f"DEBUG: Failed to parse image analysis result")
                except Exception as e:
                    print(f"DEBUG: Error analyzing image {img_url}: {e}")
        
        # 构建详细的提示词，强调保持原始颜色和款式
        detailed_prompt = f"时尚穿搭，{style}风格，{user_info}模特，穿着以下服装：{', '.join(detailed_item_descriptions)}，严格保持原始商品的颜色、款式和细节，完全忠实于原始商品的外观，精确还原商品的颜色和款式，模特姿态自然，背景简洁，高质量，真实感，清晰细节，光线自然，专业摄影效果"
        print(f"DEBUG: Generated detailed prompt: {detailed_prompt}")
        
        # 添加从图片中提取的特征
        if product_features:
            features_info = "基于以下商品图片特征生成穿搭效果："
            for feature in product_features:
                features_info += feature + "，"
            detailed_prompt = features_info + detailed_prompt
            print(f"DEBUG: Enhanced prompt with image features: {detailed_prompt}")
        
        # 构建包含多张商品图片信息的提示词
        if product_image_urls:
            image_info = "参考商品图片："
            for i, img_url in enumerate(product_image_urls[:3]):  # 最多使用3张图片
                image_info += f"图片{i+1}，"
            detailed_prompt = image_info + detailed_prompt
            print(f"DEBUG: Enhanced prompt with multiple images: {detailed_prompt}")
        
        # 使用商品图片作为基础进行图生图
        print(f"DEBUG: Using product image for image-to-image generation: {base_image_url}")
        
        # 调用图生图功能
        image_url = await llm_service.generate_image_from_image(base_image_url, detailed_prompt, size="1024x1024")
        print(f"DEBUG: Generated image URL (image-to-image): {image_url}")
        return image_url
    except Exception as e:
        print(f"DEBUG: Generate outfit image error: {e}")
        # 如果发生异常，使用默认图片
        return "https://img.alicdn.com/imgextra/i4/1924119553/O1CN01N7qEst2KRKD6zfMVz_!!1924119553.jpg"

async def format_response_node(state: AgentState) -> AgentState:
    intent_obj = state['intent']
    intent = intent_obj.intent if hasattr(intent_obj, 'intent') else str(intent_obj)
    
    if intent == 'search':
        state['response'] = {
            'intent': 'search',
            'session_id': state['session_id'],
            'keyword': state['message'],
            'filters': state['conditions'],
            'items': state['products'],
            'total': len(state['products'])
        }
    elif intent == 'recommendation':
        outfit_items = []
        for item in state['outfit'].get('items', []):
            p = item['product']
            outfit_items.append({
                'name': p.name,
                'price': p.price or 0,
                'image_url': p.image_url or '',
                'product_url': p.product_url or ''
            })
        
        style = state['conditions'].get('style', '时尚')
        try:
            message = await generate_recommendation_reason(state['message'], outfit_items, state.get('user_profile'))
        except:
            message = f"为您推荐这套{style}风格的搭配："
        
        # 生成虚拟试穿图
        outfit_image = None
        try:
            print(f"DEBUG: Before calling generate_outfit_image, outfit_items length: {len(outfit_items)}")
            outfit_image = await generate_outfit_image(outfit_items, style, state.get('user_profile'))
            print(f"DEBUG: After calling generate_outfit_image, outfit_image: {outfit_image}")
        except Exception as e:
            print(f"Error generating outfit image: {e}")
        
        print(f"DEBUG: Before creating response, outfit_image: {outfit_image}")
        state['response'] = {
            'intent': 'recommendation',
            'session_id': state['session_id'],
            'outfit_name': state['outfit'].get('outfit_name', '时尚搭配'),
            'items': outfit_items,
            'outfit_image': outfit_image,
            'filters': state['conditions'],
            'message': message
        }
        print(f"DEBUG: After creating response, response['outfit_image']: {state['response']['outfit_image']}")
    else:
        state['response'] = {
            'intent': 'general',
            'session_id': state['session_id'],
            'message': '您好！我是您的智能服装穿搭助手，请问有什么可以帮您的？'
        }
    
    return state


def should_continue(state: AgentState) -> str:
    intent = state['intent'].intent if hasattr(state['intent'], 'intent') else state['intent']
    if intent in ['search', 'recommendation']:
        return "search"
    return "end"


async def run_agent(message: str, user_id: str = "default", session_id: str = None):
    if session_id is None:
        import uuid
        session_id = str(uuid.uuid4())
    
    # Get user profile if user_id is provided
    user_profile = {}
    if user_id != "default":
        from services.user_service import UserService
        user_service = UserService()
        try:
            user = user_service.get_user(user_id)
            if user and user.profile:
                user_profile = user.profile.model_dump()
                print(f"DEBUG: User profile found: {user_profile}")
        finally:
            user_service.close()
    
    initial_state = {
        'message': message,
        'user_id': user_id,
        'session_id': session_id,
        'intent': None,
        'conditions': {},
        'products': [],
        'outfit': {},
        'response': {},
        'user_profile': user_profile
    }
    
    return await _run_agent(initial_state)


async def _run_agent(initial_state: dict):
    from agent.intent_classifier import IntentResult
    
    await intent_node_llm(initial_state)
    
    extract_conditions_node(initial_state)
    
    search_node(initial_state)
    
    recommend_node(initial_state)
    
    await format_response_node(initial_state)
    
    return initial_state['response']
