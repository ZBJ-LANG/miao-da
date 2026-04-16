import os
import json
import base64
import asyncio
import httpx
from typing import Optional, List, Dict, Any

class LLMService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('DASHSCOPE_API_KEY')
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.chat_model = "qwen-plus"
        self.vision_model = "qwen-vl-max"
        self.image_model = "stable-diffusion-xl"
    
    async def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"LLM API Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"LLM Request Error: {e}")
            return None
    
    async def vision_chat(self, image_url: str, prompt: str = None, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        default_prompt = """分析这张衣服图片，提取以下信息并以JSON格式返回：
- style: 服装风格（如：休闲、商务、运动、韩系、复古、学院等）
- color: 主色调（如：黑色、白色、蓝色、红色等）
- category: 服装类别（如：上衣、下装、连衣裙、外套、鞋子、配件等）
- season: 适合季节（如：春夏、秋冬、春夏秋冬）
- description: 简单的风格描述

只返回JSON格式，不要其他内容。"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or default_prompt
                    }
                ]
            }
        ]
        
        data = {
            "model": self.vision_model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"Vision API Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            print(f"Vision Request Error: {e}")
            return None
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> Optional[str]:
        default_image = "https://img.alicdn.com/imgextra/i4/1924119553/O1CN01N7qEst2KRKD6zfMVz_!!1924119553.jpg"
        
        print("="*50)
        print("IMAGE GENERATION STARTED")
        print(f"Prompt: {prompt}")
        
        try:
            import httpx
            
            api_key = self.api_key or os.environ.get('DASHSCOPE_API_KEY')
            print(f"API Key loaded: {api_key[:10]}...{api_key[-4:]}" if api_key else "NO API KEY")
            
            if not api_key:
                print("DEBUG: API key not found - returning default")
                return default_image
            
            size_map = {
                "1024x1024": "1024*1024",
                "1024x1536": "1024*1536", 
                "1536x1024": "1536*1024",
                "2048x2048": "2048*2048"
            }
            image_size = size_map.get(size, "1024*1024")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-DashScope-Async": "enable"
            }
            
            payload = {
                "model": "wan2.5-t2i-preview",
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "size": image_size,
                    "n": 1
                }
            }
            
            print(f"DEBUG: Wanxi API request - Model: wan2.5-t2i-preview, Prompt: {prompt}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"Sending request to dashscope...")
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                    headers=headers,
                    json=payload
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text[:500] if len(response.text) > 500 else response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get("output", {}).get("task_id")
                    if not task_id:
                        print(f"DEBUG: No task_id returned: {result}")
                        return default_image
                    
                    print(f"DEBUG: Task created, polling task_id: {task_id}")
                    
                    # 设置最大轮询次数为30次，每次2秒，总共60秒
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        await asyncio.sleep(2)
                        status_response = await client.get(
                            f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            task_status = status_result.get("output", {}).get("task_status")
                            print(f"DEBUG: Task status: {task_status} (Attempt {attempt+1}/{max_attempts})")
                            if task_status == "SUCCEEDED":
                                image_url = status_result.get("output", {}).get("results", [{}])[0].get("url")
                                if image_url:
                                    print(f"DEBUG: Generated image URL: {image_url}")
                                    return image_url
                            elif task_status in ["FAILED", "CANCELED"]:
                                print(f"DEBUG: Task failed: {status_result}")
                                return default_image
                        else:
                            print(f"DEBUG: Status check error: {status_response.text}")
                    
                    # 超时，返回默认图片
                    print(f"DEBUG: Image generation timed out after {max_attempts} attempts")
                    return default_image
                else:
                    print(f"DEBUG: API returned status code: {response.status_code}, message: {response.text}")
                    return default_image
        except Exception as e:
            print(f"DEBUG: Generate image error: {e}")
            import traceback
            traceback.print_exc()
            return default_image
    
    async def generate_image_from_image(self, image_url: str, prompt: str, size: str = "1024x1024") -> Optional[str]:
        default_image = "https://img.alicdn.com/imgextra/i4/1924119553/O1CN01N7qEst2KRKD6zfMVz_!!1924119553.jpg"
        
        print("="*50)
        print("IMAGE-TO-IMAGE GENERATION STARTED")
        print(f"Image URL: {image_url}")
        print(f"Prompt: {prompt}")
        
        try:
            import httpx
            
            api_key = self.api_key or os.environ.get('DASHSCOPE_API_KEY')
            print(f"API Key loaded: {api_key[:10]}...{api_key[-4:]}" if api_key else "NO API KEY")
            
            if not api_key:
                print("DEBUG: API key not found - returning default")
                return default_image
            
            size_map = {
                "1024x1024": "1024*1024",
                "1024x1536": "1024*1536", 
                "1536x1024": "1536*1024",
                "2048x2048": "2048*2048"
            }
            image_size = size_map.get(size, "1024*1024")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-DashScope-Async": "enable"
            }
            
            payload = {
                "model": "wan2.5-t2i-preview",
                "input": {
                    "prompt": prompt,
                    "image_url": image_url
                },
                "parameters": {
                    "size": image_size,
                    "n": 1,
                    "strength": 0.7  # 控制原图影响程度，0-1，值越大原图影响越大
                }
            }
            
            print(f"DEBUG: Wanxi API request - Model: wan2.5-t2i-preview, Image URL: {image_url}, Prompt: {prompt}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"Sending request to dashscope...")
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                    headers=headers,
                    json=payload
                )
                
                print(f"Response status: {response.status_code}")
                print(f"Response text: {response.text[:500] if len(response.text) > 500 else response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get("output", {}).get("task_id")
                    if not task_id:
                        print(f"DEBUG: No task_id returned: {result}")
                        return default_image
                    
                    print(f"DEBUG: Task created, polling task_id: {task_id}")
                    
                    # 设置最大轮询次数为30次，每次2秒，总共60秒
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        await asyncio.sleep(2)
                        status_response = await client.get(
                            f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            task_status = status_result.get("output", {}).get("task_status")
                            print(f"DEBUG: Task status: {task_status} (Attempt {attempt+1}/{max_attempts})")
                            if task_status == "SUCCEEDED":
                                image_url = status_result.get("output", {}).get("results", [{}])[0].get("url")
                                if image_url:
                                    print(f"DEBUG: Generated image URL: {image_url}")
                                    return image_url
                            elif task_status in ["FAILED", "CANCELED"]:
                                print(f"DEBUG: Task failed: {status_result}")
                                return default_image
                        else:
                            print(f"DEBUG: Status check error: {status_response.text}")
                    
                    # 超时，返回默认图片
                    print(f"DEBUG: Image generation timed out after {max_attempts} attempts")
                    return default_image
                else:
                    print(f"DEBUG: API returned status code: {response.status_code}, message: {response.text}")
                    return default_image
        except Exception as e:
            print(f"DEBUG: Generate image from image error: {e}")
            import traceback
            traceback.print_exc()
            return default_image


llm_service = LLMService()

STYLE_MAPPING = {
    '甜美': '韩系',
    '可爱': '韩系',
    '性感': '商务',
    '成熟': '商务',
    '清新': '休闲',
    '文艺': '复古',
    '少女': '韩系',
    '通勤': '商务',
    '法式': '复古',
    '法国': '复古',
    '法式复古': '复古',
    '日系': '韩系',
    '欧美': '复古',
    '运动': '运动',
    '街头': '休闲',
    '学院': '学院',
    '优雅': '复古',
}

DB_STYLES = ['休闲', '商务', '运动', '学院', '复古', '韩系']

CATEGORY_MAPPING = {
    '上装': '上衣',
    '下装': '下装',
    '裤装': '下装',
    '裙装': '连衣裙',
    '鞋子': '鞋子',
    '鞋': '鞋子',
    '配饰': '配件',
    '配': '配件',
}


def map_style_to_db(style: str) -> str:
    if style in DB_STYLES:
        return style
    if style in STYLE_MAPPING:
        return STYLE_MAPPING[style]
    
    style_lower = style.lower()
    # 优雅、成熟风格
    if '优雅' in style or '成熟' in style or '简约' in style or '都市' in style:
        return '复古'
    if '法' in style or 'french' in style_lower or ' france' in style_lower:
        return '复古'
    if '韩' in style or 'korean' in style_lower or ' korean' in style_lower:
        return '韩系'
    if '日' in style or 'japanese' in style_lower:
        return '韩系'
    if '欧美' in style or 'western' in style_lower or 'european' in style_lower:
        return '复古'
    if '运动' in style or 'sport' in style_lower or 'athletic' in style_lower:
        return '运动'
    if '学院' in style or 'preppy' in style_lower or 'academic' in style_lower:
        return '学院'
    if '商务' in style or 'business' in style_lower or 'formal' in style_lower:
        return '商务'
    if '休闲' in style or 'casual' in style_lower or 'leisure' in style_lower:
        return '休闲'
    
    return '休闲'


def map_category_to_db(category: str) -> str:
    if category in CATEGORY_MAPPING:
        return CATEGORY_MAPPING[category]
    if category in ['上衣', '下装', '连衣裙', '鞋子', '配件']:
        return category
    
    cat_lower = category.lower()
    if '上' in category or 'shirt' in cat_lower or 'top' in cat_lower or 'tee' in cat_lower:
        return '上衣'
    if '下' in category or '裤' in category or 'pants' in cat_lower or 'bottom' in cat_lower:
        return '下装'
    if '裙' in category or 'dress' in cat_lower or 'skirt' in cat_lower:
        return '连衣裙'
    if '鞋' in category or 'shoe' in cat_lower or 'sneaker' in cat_lower or 'boot' in cat_lower:
        return '鞋子'
    if '配' in category or 'bag' in cat_lower or 'hat' in cat_lower or 'accessory' in cat_lower:
        return '配件'
    
    return category


async def classify_intent_with_llm(message: str, user_profile: dict = None) -> dict:
    profile_info = ""
    if user_profile:
        profile_info = f"\n用户信息：性别{user_profile.get('gender', '')}，年龄{user_profile.get('age', '')}岁，身高{user_profile.get('height', '')}cm，体重{user_profile.get('weight', '')}kg，身材{user_profile.get('body_type', '')}"
    
    system_prompt = """你是一个智能服装穿搭助手。用户会输入一句话，你需要判断用户的意图。

可能的意图：
1. search - 用户想搜索/查找商品
2. recommendation - 用户想要穿搭推荐/搭配建议
3. image_search - 用户上传了图片，想要找类似的衣服
4. virtual_tryon - 用户想要虚拟试穿/生成效果图
5. general - 一般对话/打招呼

请以JSON格式返回结果，包含：
- intent: 意图类型
- confidence: 置信度(0-1)
- conditions: 提取的搜索条件，包括category(商品类别如上衣/下装/鞋子/配件/连衣裙)、color(颜色)、style(风格如休闲/商务/运动/韩系)、occasion(场合如约会/上班/日常)

只返回JSON，不要其他内容。"""

    user_prompt = f"用户输入：{message}{profile_info}"

    try:
        response = await llm_service.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], temperature=0.1)
        
        if response:
            result = json.loads(response)
            return {
                "intent": result.get("intent", "general"),
                "confidence": result.get("confidence", 0.5),
                "conditions": result.get("conditions", {})
            }
    except Exception as e:
        print(f"Intent classification error: {e}")
    
    return {
        "intent": "general",
        "confidence": 0.5,
        "conditions": {}
    }


async def analyze_clothing_image(image_url: str) -> dict:
    try:
        print(f"DEBUG: 开始分析图片: {image_url[:100]}...")
        
        # 检查图片URL格式
        if image_url.startswith('data:'):
            print(f"DEBUG: 处理base64图片，长度: {len(image_url)}")
        else:
            print(f"DEBUG: 处理普通URL: {image_url}")
        
        response = await llm_service.vision_chat(
            image_url,
            prompt="""分析这张衣服图片，提取以下信息并以JSON格式返回：
- style: 服装风格（如：休闲、商务、运动、韩系、复古、学院、优雅、成熟、简约、都市等）
- color: 主色调（如：黑色、白色、蓝色、红色等）
- category: 服装类别（如：上衣、下装、连衣裙、外套、鞋子、配件等）
- season: 适合季节（如：春夏、秋冬、春夏秋冬）
- description: 详细的风格描述，包括材质、款式等
- material: 服装材质（如：棉、麻、丝、缎面、皮质等）

只返回JSON格式，不要其他内容。"""
        )
        
        print(f"DEBUG: 图片分析API返回: {response[:200]}..." if response else "DEBUG: 图片分析API返回空")
        
        if response:
            try:
                result = json.loads(response)
                print(f"DEBUG: 解析后的分析结果: {result}")
                
                conditions = {}
                
                if result.get("style"):
                    conditions["style"] = map_style_to_db(result["style"])
                    print(f"DEBUG: 提取风格: {result['style']} -> {conditions['style']}")
                if result.get("color"):
                    conditions["color"] = result["color"]
                    print(f"DEBUG: 提取颜色: {result['color']}")
                if result.get("category"):
                    conditions["category"] = result["category"]
                    print(f"DEBUG: 提取类别: {result['category']}")
                if result.get("season"):
                    conditions["season"] = result["season"]
                    print(f"DEBUG: 提取季节: {result['season']}")
                
                return {
                    "success": True,
                    "conditions": conditions,
                    "description": result.get("description", ""),
                    "material": result.get("material", ""),
                    "raw_result": result
                }
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON解析错误: {e}")
                return {
                    "success": False,
                    "error": f"JSON解析错误: {e}",
                    "conditions": {},
                    "description": ""
                }
        else:
            print("DEBUG: 图片分析API返回空结果")
            return {
                "success": False,
                "error": "图片分析API返回空结果",
                "conditions": {},
                "description": ""
            }
    except Exception as e:
        print(f"DEBUG: 分析图片时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "conditions": {},
            "description": ""
        }


async def generate_recommendation_reason(message: str, outfit_items: list, user_profile: dict = None) -> str:
    if not outfit_items:
        return "为您找到以下商品"
    
    # 构建用户信息
    profile_info = ""
    if user_profile:
        gender = user_profile.get('gender', '')
        body_type = user_profile.get('body_type', '')
        age = user_profile.get('age', '')
        if gender:
            profile_info += f"{gender}性用户，"
        if age:
            profile_info += f"{age}岁，"
        if body_type:
            profile_info += f"{body_type}身材，"
    
    # 构建商品信息
    item_details = []
    for item in outfit_items[:4]:
        name = item.get("name", "")
        price = item.get("price", 0)
        item_details.append(f"{name[:25]}（¥{price}）")
    item_info = "、".join(item_details)
    
    # 构建用户请求信息
    request_info = f"用户请求：{message}"
    
    # 优化系统提示
    system_prompt = """你是一个专业、亲切的服装搭配顾问，擅长为用户提供个性化的穿搭建议。

请根据以下信息，为用户生成一段自然、亲切的推荐理由：
1. 用户信息：包括性别、年龄、身材等
2. 用户的具体请求：如场合、风格偏好等
3. 推荐的商品：包括名称和价格

要求：
- 语言自然、亲切，像朋友一样给出建议
- 突出商品的特点和搭配的优势
- 考虑用户的具体需求和场景
- 避免生硬的表达，让用户感觉温暖和专业
- 长度控制在3-4句话，不要太长
"""
    
    user_prompt = f"用户信息：{profile_info}\n{request_info}\n推荐商品：{item_info}\n\n请生成推荐理由。"

    try:
        response = await llm_service.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], temperature=0.9, max_tokens=300)
        
        if response:
            # 确保返回的内容自然流畅
            return response.strip()
    except Exception as e:
        print(f"Generate recommendation reason error: {e}")
    
    # 改进的 fallback 消息
    style = "休闲"
    if "商务" in message:
        style = "商务"
    elif "运动" in message:
        style = "运动"
    elif "学院" in message:
        style = "学院"
    elif "复古" in message:
        style = "复古"
    elif "韩系" in message:
        style = "韩系"
    
    return f"这套{style}风格的搭配特别适合您，既时尚又舒适，性价比也很高，希望您喜欢！"
