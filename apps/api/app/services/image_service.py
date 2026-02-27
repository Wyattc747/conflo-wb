"""Image processing — EXIF extraction and thumbnail generation."""

import io

from PIL import Image as PILImage
from PIL.ExifTags import GPSTAGS, TAGS
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.file import File
from app.services.file_service import BUCKET, s3_client


async def process_image(db: AsyncSession, file_record: File):
    """Extract EXIF data and generate thumbnail for image files."""
    response = s3_client.get_object(Bucket=BUCKET, Key=file_record.s3_key)
    image_bytes = response["Body"].read()

    img = PILImage.open(io.BytesIO(image_bytes))

    # Extract EXIF
    exif_data = extract_exif(img)
    if exif_data:
        file_record.exif_data = exif_data

    # Generate thumbnail (400px wide, maintain aspect ratio)
    thumbnail = generate_thumbnail(img, max_width=400)

    # Upload thumbnail to S3
    thumb_key = file_record.s3_key.replace(".", "_thumb.")
    thumb_buffer = io.BytesIO()
    thumbnail.save(thumb_buffer, format="JPEG", quality=80)
    thumb_buffer.seek(0)

    s3_client.put_object(
        Bucket=BUCKET,
        Key=thumb_key,
        Body=thumb_buffer,
        ContentType="image/jpeg",
    )

    file_record.thumbnail_key = thumb_key
    await db.flush()


def extract_exif(img: PILImage.Image) -> dict | None:
    """Extract useful EXIF data from an image."""
    try:
        raw_exif = img._getexif()
        if not raw_exif:
            return None

        exif = {}
        for tag_id, value in raw_exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == "DateTimeOriginal":
                exif["date_taken"] = str(value)
            elif tag == "Make":
                exif["camera_make"] = str(value)
            elif tag == "Model":
                exif["camera_model"] = str(value)
            elif tag == "GPSInfo":
                gps = parse_gps_info(value)
                if gps:
                    exif["gps_lat"] = gps["lat"]
                    exif["gps_lon"] = gps["lon"]
            elif tag == "ImageWidth":
                exif["width"] = value
            elif tag == "ImageLength":
                exif["height"] = value

        return exif if exif else None
    except Exception:
        return None


def generate_thumbnail(img: PILImage.Image, max_width: int = 400) -> PILImage.Image:
    """Resize image to thumbnail maintaining aspect ratio."""
    ratio = max_width / img.width
    new_height = int(img.height * ratio)
    thumbnail = img.copy()
    thumbnail.thumbnail((max_width, new_height), PILImage.LANCZOS)
    if thumbnail.mode in ("RGBA", "P"):
        thumbnail = thumbnail.convert("RGB")
    return thumbnail


def parse_gps_info(gps_info: dict) -> dict | None:
    """Parse GPS EXIF data into lat/lon."""
    try:
        gps = {}
        for key in gps_info:
            tag = GPSTAGS.get(key, key)
            gps[tag] = gps_info[key]

        lat = _gps_to_decimal(gps.get("GPSLatitude"), gps.get("GPSLatitudeRef"))
        lon = _gps_to_decimal(gps.get("GPSLongitude"), gps.get("GPSLongitudeRef"))

        if lat is not None and lon is not None:
            return {"lat": lat, "lon": lon}
        return None
    except Exception:
        return None


def _gps_to_decimal(coords, ref) -> float | None:
    """Convert GPS coordinates from degrees/minutes/seconds to decimal."""
    if not coords or not ref:
        return None
    try:
        degrees = float(coords[0])
        minutes = float(coords[1])
        seconds = float(coords[2])
        decimal = degrees + minutes / 60 + seconds / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 7)
    except (IndexError, TypeError, ValueError):
        return None
