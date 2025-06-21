import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs

load_dotenv()
API_KEY = os.getenv("TWELVE_LABS_API_KEY")
client = TwelveLabs(api_key=API_KEY)
