from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image_upload(image):
    """Validate an uploaded image's size, format, and image data."""

    if not image:
        return image

    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError("The image must be 5 MB or smaller.")

    try:
        image.seek(0)

        with Image.open(image) as img:
            image_format = img.format
            img.verify()

        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                "Upload a JPEG, PNG, or WebP image."
            )

        image.seek(0)

        # Check that the image data can actually be decoded.
        with Image.open(image) as img:
            img.load()

    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError("Upload a valid image file.")

    finally:
        image.seek(0)

    return image
