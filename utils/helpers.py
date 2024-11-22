# utils/helpers.py

import base64


def image_to_base64(img_bytes):
    """
    Encodes image bytes to a base64 string.

    Parameters:
        img_bytes (bytes): Image data in bytes.

    Returns:
        str: Base64 encoded string of the image.
    """
    return base64.b64encode(img_bytes).decode()
