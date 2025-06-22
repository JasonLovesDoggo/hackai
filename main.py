from fastapi import FastAPI, APIRouter
from services.youtube_scraper.routes import router as youtube_router
from services.video_analyzer.routes import router as video_analyzer_router
from services.affiliate_discovery.routes import router as affiliate_router
from services.video_monetization.routes import router as video_monetization_router
from services.revenue_playbook.routes import router as revenue_playbook_router
from services.groq_passthrough.routes import router as groq_router
from routes.cache import router as cache_router
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(title="HackAI - Creator Analytics Backend")

api_router = APIRouter(prefix="/api")
api_router.include_router(youtube_router)
api_router.include_router(video_analyzer_router)
api_router.include_router(affiliate_router)
api_router.include_router(video_monetization_router)
api_router.include_router(revenue_playbook_router)
api_router.include_router(groq_router)
api_router.include_router(cache_router)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "HackAI Creator Analytics API"}
