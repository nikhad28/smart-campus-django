import os
from supabase import create_client
from django.conf import settings

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return cls._instance
    
    def get_client(self):
        return self.client

# Global instance
supabase = SupabaseClient().get_client()