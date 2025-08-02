from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger, log_request
from src.api.routes import data

# Initialize logger
logger = get_ui_logger("api")

app = FastAPI(
    title="ML Trading API",
    description="API for ML Trading System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests"""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    duration = round((time.time() - start_time) * 1000, 2)
    
    # Log request details
    request_info = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration": duration
    }
    log_request(request_info, logger)
    
    return response

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "ML Trading API is running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy", "service": "ml-trading-api"}

# Include data routes
app.include_router(data.router)

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def find_free_port(start_port=8000, max_attempts=10):
        """Find a free port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return start_port  # Fallback to original port
    
    port = find_free_port(8000)
    logger.info(f"Starting FastAPI server on 0.0.0.0:{port}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port)
    except OSError as e:
        logger.error(f"Failed to start server on port {port}: {e}")
        logger.info("Trying alternative port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001) 