from fastapi import FastAPI, APIRouter
from services.youtube_scraper.routes import router as youtube_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="HackAI - Creator Analytics Backend")

api_router = APIRouter(prefix="/api")
api_router.include_router(youtube_router)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "HackAI Creator Analytics API"}
