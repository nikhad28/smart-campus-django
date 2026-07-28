import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

try:
    supabase = create_client(url, key)
    response = supabase.table('user_account').select('*').limit(1).execute()
    print("✅ Connection Successful!")
    print(f"📊 Data: {response.data}")
except Exception as e:
    print(f"❌ Connection Failed: {e}")