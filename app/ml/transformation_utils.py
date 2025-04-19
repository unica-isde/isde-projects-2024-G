import os
import time
from PIL import Image, ImageEnhance
from app.config import Configuration

conf = Configuration()

# Directory to store transformed images
TRANSFORMED_DIR = os.path.join(conf.image_folder_path, "../transformed_images")
os.makedirs(TRANSFORMED_DIR, exist_ok=True)


def transform_image(image_id: str, brightness: float, contrast: float, color: float, sharpness: float) -> str:
    """Apply transformations to the image and return new filename"""
    image_path = os.path.join(conf.image_folder_path, image_id)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image {image_id} not found")

    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
    if not image_id.lower().endswith(valid_extensions):
        raise ValueError(f"Unsupported file format. Use one of the following: {valid_extensions}")

    # Create unique filename
    timestamp = str(int(time.time()))
    base_name = os.path.splitext(image_id)[0]
    new_image_name = f"{base_name}_transformed_{timestamp}.jpg"
    dest_path = os.path.join(TRANSFORMED_DIR, new_image_name)

    try:
        with Image.open(image_path) as img:
            # Add small epsilon for floating point comparison
            epsilon = 0.001

            if abs(color - 1.0) > epsilon:
                img = ImageEnhance.Color(img).enhance(color)
            if abs(brightness - 1.0) > epsilon:
                img = ImageEnhance.Brightness(img).enhance(brightness)
            if abs(contrast - 1.0) > epsilon:
                img = ImageEnhance.Contrast(img).enhance(contrast)
            if abs(sharpness - 1.0) > epsilon:
                img = ImageEnhance.Sharpness(img).enhance(sharpness)

            img.save(dest_path, "JPEG")
        return new_image_name
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise RuntimeError(f"Transformation failed: {str(e)}")


def cleanup_transforms(max_age_seconds=30):
    """Remove transformed images older than max_age_seconds"""
    now = time.time()
    for filename in os.listdir(TRANSFORMED_DIR):
        filepath = os.path.join(TRANSFORMED_DIR, filename)
        if os.path.isfile(filepath):
            if now - os.path.getmtime(filepath) > max_age_seconds:
                os.remove(filepath)