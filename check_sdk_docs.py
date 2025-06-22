import os
from twelvelabs import TwelveLabs

def check_sdk_documentation():
    """Check the Twelve Labs SDK documentation and methods"""
    try:
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return
        
        print("✅ API key found")
        client = TwelveLabs(api_key=api_key)
        print("✅ Client initialized")
        
        # Check the client object
        print("\n📋 Client object methods:")
        for attr in dir(client):
            if not attr.startswith("_"):
                print(f"  - {attr}")
        
        # Check if there's a direct video analysis method
        print("\n🔍 Looking for video analysis methods:")
        
        # Check the task API - this might be for video analysis
        if hasattr(client, 'task'):
            print("✅ client.task exists")
            task_methods = [attr for attr in dir(client.task) if not attr.startswith("_")]
            print(f"  Task methods: {task_methods}")
            
            # Check task.create method signature
            if hasattr(client.task, 'create'):
                import inspect
                sig = inspect.signature(client.task.create)
                print(f"  Task.create signature: {sig}")
        
        # Check the index API
        if hasattr(client, 'index'):
            print("✅ client.index exists")
            index_methods = [attr for attr in dir(client.index) if not attr.startswith("_")]
            print(f"  Index methods: {index_methods}")
        
        # Check if there's a direct video analysis method
        if hasattr(client, 'video'):
            print("✅ client.video exists")
            video_methods = [attr for attr in dir(client.video) if not attr.startswith("_")]
            print(f"  Video methods: {video_methods}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_sdk_documentation() 