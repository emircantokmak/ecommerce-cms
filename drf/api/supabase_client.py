"""Supabase istemcisini yalnızca Storage işlemi gerektiğinde yükler."""
import os
from functools import lru_cache

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "product-images")


@lru_cache(maxsize=1)
def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise RuntimeError("Supabase depolama ayarları yapılmamış. .env dosyasını kontrol edin.")
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
