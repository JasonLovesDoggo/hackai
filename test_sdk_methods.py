import os
from twelvelabs import TwelveLabs

def test_sdk_methods():
    """Test what methods are available in the Twelve Labs SDK"""
    try:
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return
        
        print("✅ API key found")
        client = TwelveLabs(api_key=api_key)
        print("✅ Client initialized")
        
        # Print all available attributes and methods
        print("\n📋 Available attributes and methods:")
        for attr in dir(client):
            if not attr.startswith('_'):
                print(f"  - {attr}")
        
        # Test specific methods if they exist
        print("\n🔍 Testing specific methods:")
        
        if hasattr(client, 'index'):
            print("✅ client.index exists")
            index_methods = [attr for attr in dir(client.index) if not attr.startswith('_')]
            print(f"  Index methods: {index_methods}")
        
        if hasattr(client, 'task'):
            print("✅ client.task exists")
            task_methods = [attr for attr in dir(client.task) if not attr.startswith('_')]
            print(f"  Task methods: {task_methods}")
        
        if hasattr(client, 'video'):
            print("✅ client.video exists")
            video_methods = [attr for attr in dir(client.video) if not attr.startswith('_')]
            print(f"  Video methods: {video_methods}")
        
        if hasattr(client, 'understanding'):
            print("✅ client.understanding exists")
            understanding_methods = [attr for attr in dir(client.understanding) if not attr.startswith('_')]
            print(f"  Understanding methods: {understanding_methods}")
        
        # Try to find the correct method for video analysis
        print("\n🎯 Looking for video analysis methods:")
        
        # Check if there's a direct method on the client
        for attr in dir(client):
            if not attr.startswith('_') and 'video' in attr.lower():
                print(f"  Found video-related method: {attr}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_sdk_methods() 