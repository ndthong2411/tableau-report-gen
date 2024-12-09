# utils/helpers.py

import base64
import logzero
from logzero import logger

def image_to_base64(image_bytes):
    try:
        return base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to convert image to base64: {e}")
        return ""


