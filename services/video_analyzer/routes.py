from main import router


@router.get("/video-analyzer")
async def video_analyzer():
	return {"message": "Video Analyzer Service is running"}