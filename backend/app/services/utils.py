import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile) -> Tuple[str, str]:
    """
    Saves the uploaded file to disk with a UUID filename to prevent collisions/encoding issues.
    Returns:
        (web_path, absolute_path)
        web_path: relative path for URL (e.g. /uploads/uuid.jpg)
        absolute_path: full filesystem path for processing
    """
    try:
        ext = os.path.splitext(upload_file.filename)[1]
        if not ext:
            ext = ".jpg"
            
        new_filename = f"{uuid.uuid4()}{ext}"
        file_path = UPLOAD_DIR / new_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return f"/uploads/{new_filename}", str(file_path)
    finally:
        upload_file.file.seek(0)

def _get_if_exist(data, key):
    if key in data:
        return data[key]
    return None

def _convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format
    """
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])

    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data function)
    """
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, "GPSLatitudeRef")
        gps_longitude = _get_if_exist(gps_info, "GPSLongitude")
        gps_longitude_ref = _get_if_exist(gps_info, "GPSLongitudeRef")

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

    return lat, lon

def extract_exif_location(image_path: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts latitude and longitude from an image file using EXIF data.
    """
    try:
        image = Image.open(image_path)
        exif_data = {}
        if hasattr(image, '_getexif'):
            exif_info = image._getexif()
            if exif_info:
                for tag, value in exif_info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        gps_data = {}
                        for t in value:
                            sub_decoded = GPSTAGS.get(t, t)
                            gps_data[sub_decoded] = value[t]
                        exif_data[decoded] = gps_data
                    else:
                        exif_data[decoded] = value
        
        lat, lon = get_lat_lon(exif_data)
        return lat, lon
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        return None, None
