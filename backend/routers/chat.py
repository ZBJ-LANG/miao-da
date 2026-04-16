import logging
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import uuid

from agent.agent import run_agent
from agent.llm_service import analyze_clothing_image, map_style_to_db, map_category_to_db
from agent.skills.recommendation import search_products_by_conditions
from agent.intent_classifier import extract_search_conditions

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("backend.chat")


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    session_id: Optional[str] = None
    image_url: Optional[str] = None


class ImageSearchRequest(BaseModel):
    image_url: str
    user_id: str = "default"
    session_id: Optional[str] = None


@router.post("/")
async def chat(request: ChatRequest):
    logger.info(f"Chat request received: user_id={request.user_id}, message_length={len(request.message)}, has_image={bool(request.image_url)}")
    
    if request.session_id is None:
        session_id = str(uuid.uuid4())
        logger.info(f"Generated new session_id: {session_id}")
    else:
        session_id = request.session_id
        logger.info(f"Using existing session_id: {session_id}")
    
    if request.image_url:
        logger.info(f"Processing image URL: {request.image_url[:50]}...")
        try:
            analysis_result = await analyze_clothing_image(request.image_url)
            logger.info(f"Image analysis result: {analysis_result.get('success')}")
            
            if analysis_result.get("success"):
                conditions = analysis_result.get("conditions", {})
                logger.info(f"Extracted conditions: {conditions}")
                
                if conditions.get('style'):
                    old_style = conditions['style']
                    conditions['style'] = map_style_to_db(conditions['style'])
                    logger.info(f"Mapped style: {old_style} -> {conditions['style']}")
                if conditions.get('category'):
                    old_cat = conditions['category']
                    conditions['category'] = map_category_to_db(conditions['category'])
                    logger.info(f"Mapped category: {old_cat} -> {conditions['category']}")
                
                text_conditions = extract_search_conditions(request.message)
                logger.info(f"Extracted text conditions: {text_conditions}")
                
                for key, value in text_conditions.items():
                    if key not in conditions:
                        conditions[key] = value
                        logger.info(f"Added text condition: {key}={value}")
                
                # Search with style only first
                search_conditions = {'style': conditions.get('style')}
                logger.info(f"First search with conditions: {search_conditions}")
                products = search_products_by_conditions(search_conditions, limit=20)
                logger.info(f"First search found {len(products)} products")
                
                # If no results, try with color
                if not products and conditions.get('color'):
                    search_conditions = {'style': conditions.get('style'), 'color': conditions.get('color')}
                    logger.info(f"Second search with conditions: {search_conditions}")
                    products = search_products_by_conditions(search_conditions, limit=20)
                    logger.info(f"Second search found {len(products)} products")
                
                # If still no results, try just category
                if not products and conditions.get('category'):
                    search_conditions = {'category': conditions.get('category')}
                    logger.info(f"Third search with conditions: {search_conditions}")
                    products = search_products_by_conditions(search_conditions, limit=20)
                    logger.info(f"Third search found {len(products)} products")
                
                items = [
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
                logger.info(f"Created {len(items)} items for response")
                
                # 构建完整的穿搭推荐
                logger.info("Building complete outfit recommendation")
                from agent.skills.recommendation import generate_outfit_from_products
                from agent.agent import generate_outfit_image
                
                # 分析图片中的材质
                material = analysis_result.get("material", "")
                logger.info(f"Extracted material: {material}")
                
                # 创建完整的穿搭组合
                outfit_name = f"基于图片的{conditions.get('style', '时尚')}风格搭配"
                outfit = generate_outfit_from_products(
                    products,
                    style=conditions.get('style', '休闲')
                )
                logger.info(f"Created outfit: {outfit_name}")
                
                # 生成虚拟试穿图
                outfit_image = None
                try:
                    outfit_items = []
                    for item in outfit.get('items', []):
                        product = item.get('product')
                        if product:
                            outfit_items.append({
                                'name': product.name,
                                'price': product.price or 0,
                                'image_url': product.image_url or '',
                                'product_url': product.product_url or '',
                                'category': product.category,
                                'color': product.color,
                                'style': product.style
                            })
                    logger.info(f"Generating outfit image with {len(outfit_items)} items")
                    outfit_image = await generate_outfit_image(outfit_items, conditions.get('style', '休闲'), {})
                    logger.info(f"Generated outfit image: {outfit_image}")
                except Exception as e:
                    logger.error(f"Error generating outfit image: {e}")
                
                # 准备返回给前端的商品列表
                response_items = []
                for item in outfit.get('items', []):
                    product = item.get('product')
                    if product:
                        response_items.append({
                            'name': product.name,
                            'price': product.price or 0,
                            'image_url': product.image_url or '',
                            'product_url': product.product_url or '',
                            'category': product.category,
                            'color': product.color,
                            'style': product.style
                        })
                
                # 生成推荐理由
                from agent.llm_service import generate_recommendation_reason
                message = await generate_recommendation_reason(
                    f"基于图片分析的{conditions.get('style', '时尚')}风格穿搭推荐，材质：{material}", 
                    response_items
                )
                logger.info(f"Generated recommendation reason")
                
                response = {
                    'intent': 'recommendation',
                    'session_id': session_id,
                    'outfit_name': outfit_name,
                    'filters': conditions,
                    'items': response_items,
                    'outfit_image': outfit_image,
                    'total': len(response_items),
                    'analysis': analysis_result.get("description", ""),
                    'message': f"{message}\n\n📷 图片分析：{analysis_result.get('description', '')}\n\n材质：{material}"
                }
                logger.info(f"Returning outfit recommendation response with {len(response_items)} items")
                return response
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(status_code=500, detail="处理图片时出错")
    
    logger.info("Processing text-only request")
    try:
        result = await run_agent(request.message, request.user_id, session_id)
        logger.info(f"Agent returned result: {result.get('intent')}")
        return result
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        raise HTTPException(status_code=500, detail="处理请求时出错")


@router.post("/image-search")
async def image_search(request: ImageSearchRequest):
    logger.info(f"Image search request received: user_id={request.user_id}, image_url={request.image_url[:50]}...")
    
    if request.session_id is None:
        session_id = str(uuid.uuid4())
        logger.info(f"Generated new session_id: {session_id}")
    else:
        session_id = request.session_id
        logger.info(f"Using existing session_id: {session_id}")
    
    try:
        analysis_result = await analyze_clothing_image(request.image_url)
        logger.info(f"Image analysis result: {analysis_result.get('success')}")
        
        if not analysis_result.get("success"):
            logger.warning("Image analysis failed")
            raise HTTPException(status_code=400, detail="图片分析失败，请更换图片重试")
        
        conditions = analysis_result.get("conditions", {})
        logger.info(f"Extracted conditions: {conditions}")
        
        if conditions.get('style'):
            old_style = conditions['style']
            conditions['style'] = map_style_to_db(conditions['style'])
            logger.info(f"Mapped style: {old_style} -> {conditions['style']}")
        if conditions.get('category'):
            old_cat = conditions['category']
            conditions['category'] = map_category_to_db(conditions['category'])
            logger.info(f"Mapped category: {old_cat} -> {conditions['category']}")
        
        # Search with style only (category from vision often doesn't match DB)
        search_conditions = {'style': conditions.get('style')}
        logger.info(f"First search with conditions: {search_conditions}")
        products = search_products_by_conditions(search_conditions, limit=20)
        logger.info(f"First search found {len(products)} products")
        
        # If no results, try with color
        if not products and conditions.get('color'):
            search_conditions = {'style': conditions.get('style'), 'color': conditions.get('color')}
            logger.info(f"Second search with conditions: {search_conditions}")
            products = search_products_by_conditions(search_conditions, limit=20)
            logger.info(f"Second search found {len(products)} products")
        
        # If still no results, try just category
        if not products and conditions.get('category'):
            search_conditions = {'category': conditions.get('category')}
            logger.info(f"Third search with conditions: {search_conditions}")
            products = search_products_by_conditions(search_conditions, limit=20)
            logger.info(f"Third search found {len(products)} products")
        
        # 构建完整的穿搭推荐
        logger.info("Building complete outfit recommendation")
        from agent.skills.recommendation import generate_outfit_from_products
        from agent.agent import generate_outfit_image
        
        # 分析图片中的材质
        material = analysis_result.get("material", "")
        logger.info(f"Extracted material: {material}")
        
        # 创建完整的穿搭组合
        outfit_name = f"基于图片的{conditions.get('style', '时尚')}风格搭配"
        outfit = generate_outfit_from_products(
            products,
            style=conditions.get('style', '休闲')
        )
        logger.info(f"Created outfit: {outfit_name}")
        
        # 生成虚拟试穿图
        outfit_image = None
        try:
            outfit_items = []
            for item in outfit.get('items', []):
                product = item.get('product')
                if product:
                    outfit_items.append({
                        'name': product.name,
                        'price': product.price or 0,
                        'image_url': product.image_url or '',
                        'product_url': product.product_url or '',
                        'category': product.category,
                        'color': product.color,
                        'style': product.style
                    })
            logger.info(f"Generating outfit image with {len(outfit_items)} items")
            outfit_image = await generate_outfit_image(outfit_items, conditions.get('style', '休闲'), {})
            logger.info(f"Generated outfit image: {outfit_image}")
        except Exception as e:
            logger.error(f"Error generating outfit image: {e}")
        
        # 准备返回给前端的商品列表
        response_items = []
        for item in outfit.get('items', []):
            product = item.get('product')
            if product:
                response_items.append({
                    'name': product.name,
                    'price': product.price or 0,
                    'image_url': product.image_url or '',
                    'product_url': product.product_url or '',
                    'category': product.category,
                    'color': product.color,
                    'style': product.style
                })
        
        # 生成推荐理由
        from agent.llm_service import generate_recommendation_reason
        message = await generate_recommendation_reason(
            f"基于图片分析的{conditions.get('style', '时尚')}风格穿搭推荐，材质：{material}", 
            response_items
        )
        logger.info(f"Generated recommendation reason")
        
        response = {
            'intent': 'recommendation',
            'session_id': session_id,
            'outfit_name': outfit_name,
            'filters': conditions,
            'items': response_items,
            'outfit_image': outfit_image,
            'total': len(response_items),
            'analysis': analysis_result.get("description", ""),
            'message': f"{message}\n\n📷 图片分析：{analysis_result.get('description', '')}\n\n材质：{material}"
        }
        logger.info(f"Returning outfit recommendation response with {len(response_items)} items")
        return response
    except Exception as e:
        logger.error(f"Error processing image search: {str(e)}")
        raise HTTPException(status_code=500, detail="处理图片搜索时出错")


@router.post("/tryon")
async def virtual_tryon(message: str, cloth_image: Optional[str] = None, user_id: str = "default"):
    logger.info(f"Virtual tryon request received: user_id={user_id}, has_image={bool(cloth_image)}")
    response = {
        'intent': 'virtual_tryon',
        'message': '虚拟试穿功能正在开发中，敬请期待！',
        'outfit_image': None
    }
    logger.info("Returning virtual tryon response")
    return response
