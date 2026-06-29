import logging
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import init_db
from app.routes import session, application, pricing, recommendation, order, report, ai, admission, university, config, schools, gaokao_recommend, chat_context, province_config, jiangsu_recommend, membership, chat
from app.api.chsi_rag import router as chsi_rag_router
from app.api.school_detail import router as school_detail_router
from app.api.rag_chat import router as rag_chat_router

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="志愿参谋 API",
    docs_url="/docs",
)

# Include all routers
app.include_router(session.router)
app.include_router(application.router)
app.include_router(pricing.router)
app.include_router(recommendation.router)
app.include_router(order.router)
app.include_router(report.router)
app.include_router(ai.router)
app.include_router(admission.router)
app.include_router(university.router)
app.include_router(config.router)
app.include_router(schools.router)
app.include_router(gaokao_recommend.router)
app.include_router(chat_context.router)
app.include_router(province_config.router)
app.include_router(jiangsu_recommend.router)
app.include_router(membership.router)
app.include_router(chat.router)
if chsi_rag_router is not None:
    app.include_router(chsi_rag_router)
if school_detail_router is not None:
    app.include_router(school_detail_router)
if rag_chat_router is not None:
    app.include_router(rag_chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")


@app.get(f"{settings.api_prefix}/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}


# --- Serve frontend SPA ---
if os.path.isdir(FRONTEND_DIST):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        from fastapi.responses import Response
        
        # Don't intercept API paths
        if full_path.startswith("api/"):
            return Response(status_code=404)
        
        # Determine the file to serve
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            resp = FileResponse(file_path)
        elif os.path.exists(index_path := os.path.join(FRONTEND_DIST, "index.html")):
            resp = FileResponse(index_path, media_type="text/html")
        else:
            return {"error": "frontend not built"}
        
        # Prevent browser caching of HTML (JS/CSS have content hashes)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
