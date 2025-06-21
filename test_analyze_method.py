import os
from twelvelabs import TwelveLabs

def test_analyze_method():
    """Test the analyze method in the Twelve Labs SDK"""
    try:
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return
        
        print("✅ API key found")
        client = TwelveLabs(api_key=api_key)
        print("✅ Client initialized")
        
        # Check the analyze method
        print("\n🔍 Testing analyze method:")
        if hasattr(client, 'analyze'):
            print("✅ client.analyze exists")
            
            # Get method signature
            import inspect
            sig = inspect.signature(client.analyze)
            print(f"  Analyze method signature: {sig}")
            
            # Try to get help/docstring
            if client.analyze.__doc__:
                print(f"  Analyze docstring: {client.analyze.__doc__[:200]}...")
            
            # Test with a simple call to see what parameters it expects
            print("\n🧪 Testing analyze method call...")
            try:
                # Try to call analyze with minimal parameters
                result = client.analyze(
                    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    features=["conversation", "visual"]
                )
                print(f"✅ Analyze call successful: {type(result)}")
                print(f"  Result: {result}")
            except Exception as e:
                print(f"❌ Analyze call failed: {str(e)}")
                print(f"  Error type: {type(e)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_analyze_method() 