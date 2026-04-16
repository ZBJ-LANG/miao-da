import logging
import os
import sys
import httpx
from datetime import datetime

# 配置日志
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 创建文件处理器，使用UTF-8编码
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 创建流处理器，使用UTF-8编码
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 配置根日志器
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)

logger = logging.getLogger(__name__)

class LogStep:
    """上下文管理器，用于记录步骤的开始和结束"""
    def __init__(self, step_name):
        self.step_name = step_name
    
    def __enter__(self):
        logger.info(f"开始步骤: {self.step_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"步骤失败: {self.step_name} - 错误: {exc_val}")
        else:
            logger.info(f"步骤成功: {self.step_name}")
        return False

def check_backend():
    """检查后端服务是否运行"""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("后端服务运行正常")
            return True
        else:
            logger.error(f"后端服务返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"无法连接到后端服务: {e}")
        return False

def check_frontend():
    """检查前端服务是否运行"""
    try:
        response = httpx.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            logger.info("前端服务运行正常")
            return True
        else:
            logger.error(f"前端服务返回错误状态码: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"无法连接到前端服务: {e}")
        return False

def test_recommendation():
    """测试推荐功能"""
    try:
        logger.info("正在发送推荐请求: 五一出游穿搭")
        response = httpx.post(
            "http://localhost:8000/api/chat/",
            json={"message": "五一出游穿搭", "session_id": "test_session"},
            timeout=30
        )
        
        logger.info(f"推荐请求返回状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("推荐请求返回数据: 成功")
            
            if "items" in data and len(data["items"]) > 0:
                logger.info(f"推荐了 {len(data['items'])} 个商品")
                
                # 记录推荐的商品详情
                for i, item in enumerate(data["items"]):
                    logger.info(f"商品 {i+1}: {item['name']} - ¥{item['price']}")
                    logger.info(f"  图片URL: {item['image_url']}")
                
                if "outfit_image" in data and data["outfit_image"]:
                    logger.info("生图功能测试成功")
                    logger.info(f"生成的图片URL: {data['outfit_image']}")
                    
                    # 分析生图URL中的prompt
                    import urllib.parse
                    outfit_image = data["outfit_image"]
                    if "prompt=" in outfit_image:
                        prompt_part = outfit_image.split("prompt=")[1].split("&")[0]
                        prompt = urllib.parse.unquote(prompt_part)
                        logger.info(f"生图使用的prompt: {prompt[:100]}...")
                else:
                    logger.warning("生图功能未返回图片")
                
                if "message" in data:
                    logger.info(f"推荐理由: {data['message'][:100]}...")
                
                return True
            else:
                logger.error("推荐功能未返回商品")
                return False
        else:
            logger.error(f"推荐功能返回错误状态码: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return False
    except Exception as e:
        logger.error(f"测试推荐功能时出错: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False

def run_tests():
    """运行所有测试"""
    with LogStep("检查后端服务"):
        backend_ok = check_backend()
        if not backend_ok:
            raise Exception("后端服务未运行")
    
    with LogStep("检查前端服务"):
        frontend_ok = check_frontend()
        if not frontend_ok:
            raise Exception("前端服务未运行")
    
    with LogStep("测试推荐功能"):
        recommendation_ok = test_recommendation()
        if not recommendation_ok:
            raise Exception("推荐功能测试失败")

if __name__ == "__main__":
    logger.info("开始运行系统测试")
    try:
        run_tests()
        logger.info("系统测试完成，所有功能正常")
    except Exception as e:
        logger.error(f"系统测试失败: {e}")
    logger.info("系统测试结束")
