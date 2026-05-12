import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load .env into process environment BEFORE any SDK reads os.environ
# The OpenAI Agents SDK reads OPENAI_API_KEY directly from os.environ,
# not from pydantic-settings.
load_dotenv()

from app.core.config import settings
from app.core.logger import setup_logger
from app.database.main_db_connection import create_main_pool, close_main_pool
from app.database.collection_db_connection import create_collection_pool, close_collection_pool
from app.api.routes.health_controller import router as health_router
from app.api.routes.precaution_controller import router as precaution_router

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle: startup and shutdown.
    """
    # --- STARTUP ---
    logger.info(f"Starting {settings.service_name} on port {settings.app_port}")
    
    # Step 2 & 3: Main Operational Database
    await create_main_pool()
    logger.info("Main database connected")
    
    # Step 4 & 5: Collection Database
    await create_collection_pool()
    logger.info("Collection database connected")
    
    # Step 6: Trigger singleton creation for the AI Agent
    from app.agent.precaution_agent import precaution_agent
    
    # Step 7: Ready log
    logger.info(f"{settings.service_name} ready. Model: {settings.openai_model}")
    
    yield
    
    # --- SHUTDOWN ---
    logger.info("Shutting down...")
    await close_main_pool()
    await close_collection_pool()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ClimaSync Precaution Definer Agent",
    description=(
        "Generates prioritized disaster precaution plans with exact quantities "
        "and writes tasks to the main operational database."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env.lower() == "development" else None,
    redoc_url="/redoc" if settings.app_env.lower() == "development" else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(precaution_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env.lower() == "development"
    )
