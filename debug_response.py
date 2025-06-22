import os
import time
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
import datetime

load_dotenv()

def debug_response():
    """Debug the Twelve Labs API response structure"""
    try:
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("❌ No API key found")
            return
        
        print("✅ API key found")
        client = TwelveLabs(api_key=api_key)
        print("✅ Client initialized")
        
        # Create a simple test to see the response structure
        print("\n🔍 Testing API response structure:")
        
        # Create an index with the correct format
        print("1. Creating index...")
        index = client.index.create(
            name=f"Debug Test - {datetime.datetime.now().isoformat()}",
            models=[{"name": "marengo2.7", "options": ["visual", "audio"]}]
        )
        print(f"✅ Index created: {index.id}")
        print(f"   Index type: {type(index)}")
        print(f"   Index attributes: {dir(index)}")
        
        # Try to get the index details
        print("\n2. Getting index details...")
        index_details = client.index.retrieve(index.id)
        print(f"✅ Index details retrieved")
        print(f"   Type: {type(index_details)}")
        print(f"   Attributes: {dir(index_details)}")
        print(f"   Status: {index_details.status}")
        
        # Try to access common attributes
        print("\n3. Testing attribute access:")
        for attr in ['id', 'name', 'status', 'created_at', 'updated_at']:
            if hasattr(index_details, attr):
                value = getattr(index_details, attr)
                print(f"   {attr}: {value} (type: {type(value)})")
            else:
                print(f"   {attr}: Not found")
        
        # Test if it can be converted to dict
        print("\n4. Testing dict conversion:")
        try:
            if hasattr(index_details, 'to_dict'):
                dict_data = index_details.to_dict()
                print(f"   to_dict() method exists: {dict_data}")
            elif hasattr(index_details, '__dict__'):
                dict_data = index_details.__dict__
                print(f"   __dict__ available: {dict_data}")
            else:
                print("   No dict conversion method found")
        except Exception as e:
            print(f"   Error converting to dict: {e}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_response() 