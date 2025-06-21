from main import api_router


@api_router.get("/video-analyzer")
async def video_analyzer():
	return {"message": "Video Analyzer Service is running"}