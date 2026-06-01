from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat
from app.middlewares.tracking_middleware import TrackingMiddleware
from app.monitoring.logger import app_logger
from app.monitoring.metrics import metrics_collector

app = FastAPI(
    title="Chatbot Backend MVP",
    description="FastAPI Backend MVP to test the Mimo API connection with guardrails and telemetry placeholders.",
    version="1.0.0"
)

# 1. Mount Custom Middlewares
app.add_middleware(TrackingMiddleware)

# 2. CORS Middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Routers
app.include_router(chat.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Chatbot Backend MVP is running successfully."
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "model": chat.llm_service.default_model
    }

@app.get("/api/metrics")
async def get_metrics():
    """Exposes mock system metrics accumulated during the session."""
    return metrics_collector.get_summary()

app_logger.info("FastAPI Application initialized and running!")
