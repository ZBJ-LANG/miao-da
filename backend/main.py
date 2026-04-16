import logging
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from routers import user, product, wardrobe, search, chat
from services.database import init_db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/backend.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("backend")

app = FastAPI(
    title="智能服装穿搭助手 API",
    description="基于AI的个人服装搭配助手后端服务",
    version="1.0.0"
)

# 中间件：记录请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Received request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request completed: {request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {request.method} {request.url} - {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(product.router)
app.include_router(wardrobe.router)
app.include_router(search.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup_event():
    logger.info("Starting up backend service...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
    logger.info("Backend service started successfully")


@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "智能服装穿搭助手 API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting backend service with uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000)
