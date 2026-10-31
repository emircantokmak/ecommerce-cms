
import uuid
from pathlib import Path

from api.supabase_client import get_supabase_client, SUPABASE_BUCKET_NAME


ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def upload_product_image(image_file):
    supabase = get_supabase_client()
    content_type = getattr(image_file, "content_type", None)

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Yalnızca JPEG, PNG ve WebP görseller yüklenebilir.")

    extension = ALLOWED_CONTENT_TYPES[content_type]
    file_path = f"products/{uuid.uuid4().hex}{extension}"

    image_file.seek(0)
    file_bytes = image_file.read()

    try:
        supabase.storage.from_(SUPABASE_BUCKET_NAME).upload(
            file_path,
            file_bytes,
            {
                "content-type": content_type,
                "upsert": "false",
            },
        )
    finally:
        image_file.seek(0)

    return supabase.storage.from_(
        SUPABASE_BUCKET_NAME
    ).get_public_url(file_path)


def delete_product_image(image_url):
    marker = f"/storage/v1/object/public/{SUPABASE_BUCKET_NAME}/"

    if marker not in image_url:
        return

    file_path = image_url.split(marker, 1)[1].split("?", 1)[0]

    if file_path:
        supabase = get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET_NAME).remove([file_path])