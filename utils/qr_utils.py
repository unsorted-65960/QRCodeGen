# utils/qr_utils.py
import qrcode
from PIL import Image
import os

def generate_qr_image(data_text: str) -> Image.Image:
    """
    Generate a PIL Image for the given text with a robust error correction level.
    """
    qr = qrcode.QRCode(
        version=None,  # automatic fit
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4
    )
    qr.add_data(data_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")

def save_qr_image(img: Image.Image, save_path: str):
    """
    Save PIL Image to disk creating directories as needed.
    """
    dirpath = os.path.dirname(save_path)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    img.save(save_path)
