from twelvelabs.models import Task

from .api_client import client
from pytube import YouTube
import os

FEATURES = ["conversation", "visual", "text_in_video", "action", "concept"]


def get_or_create_index(name="default-index"):
    indexes = client.index.list()
    for idx in indexes:
        if idx.name == name:
            return idx
    return client.index.create(
        name=name, models=[{"name": "marengo2.7", "options": ["visual", "audio"]}]
    )


def upload_video(video_url):
    # Download or stream to local file; here we assume local .mp4
    return client.task.create(
        index_id=get_or_create_index().id, file=video_url, language="en"
    )


def extract_insights(video_id):
    gist = client.gist(video_id=video_id, types=["title", "topic", "hashtag"])
    summary = client.summarize(video_id, type="summary", prompt="Bullet summary")
    return {
        "title": gist.title,
        "topics": gist.topics,
        "hashtags": gist.hashtags,
        "summary": summary.summary,
    }


def analyze_youtube_video(youtube_url: str) -> dict:
    file_path = download_youtube_video(youtube_url)

    task: Task = upload_video(file_path)
    task.wait_for_done()
    video_id = task.video_id

    insights = extract_insights(video_id)

    return {"video_id": video_id, **insights}


def download_youtube_video(youtube_url: str, output_dir="downloads") -> str:
    os.makedirs(output_dir, exist_ok=True)
    yt = YouTube(youtube_url)
    stream = (
        yt.streams.filter(progressive=True, file_extension="mp4")
        .order_by("resolution")
        .desc()
        .first()
    )
    file_path = stream.download(output_path=output_dir)
    return file_path
