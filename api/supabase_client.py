
import os

from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_BUCKET_NAME = os.getenv(
    "SUPABASE_BUCKET_NAME",
    "product-images"
)


if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing from .env")

if not SUPABASE_SECRET_KEY:
    raise ValueError("SUPABASE_SECRET_KEY is missing from .env")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)