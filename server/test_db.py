import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import urllib.request
import urllib.error

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

async def test_connection():
    print(f"Testing connection to: {SUPABASE_URL}")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY is missing in .env")
        return

    # Test 1: Basic HTTP Request
    print("\n--- Test 1: Basic HTTP Request ---")
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/", 
            headers={"apikey": SUPABASE_KEY}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"HTTP Status: {response.status}")
            if response.status == 200:
                print("Basic HTTP connection successful.")
            else:
                print(f"Basic HTTP connection returned status: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"Basic HTTP connection failed with HTTP error: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"Basic HTTP connection failed with URL error: {e.reason}")
    except Exception as e:
        print(f"Basic HTTP connection failed: {e}")

    # Test 2: Supabase Client
    print("\n--- Test 2: Supabase Client ---")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try a simple query
        response = supabase.table("users").select("*").limit(1).execute()
        
        print("Supabase client connection successful!")
        print(f"Query result: {response}")
        
    except Exception as e:
        print(f"Supabase client connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection())
