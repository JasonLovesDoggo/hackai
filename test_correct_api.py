import os
import time
from twelvelabs import TwelveLabs


def test_correct_api_flow():
    """Test the correct Twelve Labs API flow for video analysis"""
    try:
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return

        print("✅ API key found")
        client = TwelveLabs(api_key=api_key)
        print("✅ Client initialized")

        print("\n🔍 Testing correct API flow:")

        # Step 1: Create an index
        print("1. Creating index...")
        try:
            index = client.index.create(
                name="test-video-analysis", models=["gpt-4o-mini"]
            )
            print(f"✅ Index created with ID: {index.id}")

            # Step 2: Add a video to the index
            print("2. Adding video to index...")
            video = client.index.video.create(
                index_id=index.id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            )
            print(f"✅ Video added with ID: {video.id}")

            # Step 3: Wait for processing
            print("3. Waiting for video processing...")
            while True:
                status = client.index.retrieve(index.id)
                print(f"   Index status: {status.status}")

                if status.status == "ready":
                    print("✅ Index is ready!")
                    break
                elif status.status == "failed":
                    print("❌ Index processing failed")
                    return

                time.sleep(5)

            # Step 4: Get video details
            print("4. Getting video details...")
            videos = client.index.video.list(index_id=index.id)
            if videos.data:
                video_id = videos.data[0].id
                print(f"✅ Found video with ID: {video_id}")

                # Step 5: Get analysis results
                print("5. Getting analysis results...")
                # Try to get the video analysis
                video_details = client.index.video.retrieve(
                    index_id=index.id, video_id=video_id
                )
                print(f"✅ Video details: {video_details}")

            else:
                print("❌ No videos found in index")

        except Exception as e:
            print(f"❌ Error in API flow: {str(e)}")
            print(f"  Error type: {type(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    test_correct_api_flow()
