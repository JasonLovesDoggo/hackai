import os
import asyncio
from services.video_analyzer.api_client import TwelveLabsAPIClient


async def test_api_key():
    try:
        print("Testing Twelve Labs API key...")

        # Check environment variable
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if api_key:
            print(f"✅ API key found: {api_key[:10]}...")
        else:
            print("❌ No API key found in environment")
            return

        async with TwelveLabsAPIClient() as client:
            print("✅ API client initialized successfully")

            try:
                response = await client.client.get(
                    "https://api.twelvelabs.io/v2/indexes", headers=client.headers
                )

                print(f"Response Status: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text[:500]}...")

                if response.status_code == 200:
                    print(
                        "✅ API key is valid - successfully connected to Twelve Labs API"
                    )
                    data = response.json()
                    print(f"Found {len(data.get('data', []))} existing indexes")
                elif response.status_code == 401:
                    print("❌ API key is invalid - authentication failed")
                elif response.status_code == 404:
                    print("⚠️ 404 error - checking if endpoint is correct")
                    # Try alternative endpoint
                    alt_response = await client.client.get(
                        "https://api.twelvelabs.io/v2/indexes/", headers=client.headers
                    )
                    print(f"Alternative endpoint response: {alt_response.status_code}")
                else:
                    print(
                        f"⚠️ Unexpected response: {response.status_code} - {response.text}"
                    )

            except Exception as e:
                print(f"❌ Error testing API connection: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def test_with_official_sdk():
    try:
        print("\nTesting with official Twelve Labs SDK...")

        try:
            from twelvelabs import TwelveLabs

            print("✅ Official SDK imported successfully")

            api_key = os.getenv("TWELVE_LABS_API_KEY")
            if not api_key:
                print("❌ No API key found")
                return

            client = TwelveLabs(api_key=api_key)
            print("✅ Official SDK client initialized")

            try:
                indexes = client.index.list()
                print(f"✅ Successfully listed indexes: {len(indexes.data)} found")
                return True
            except Exception as e:
                print(f"❌ Error listing indexes with SDK: {str(e)}")
                return False

        except ImportError:
            print("❌ Official Twelve Labs SDK not available")
            return False

    except Exception as e:
        print(f"❌ Error with official SDK: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(test_api_key())
    asyncio.run(test_with_official_sdk())
