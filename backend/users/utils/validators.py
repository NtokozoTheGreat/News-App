from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError
import ipaddress
from urllib.parse import urlsplit
from django.core.validators import URLValidator

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


def validate_website_url(url):

    if not url:
        return url

    url = url.strip()

    if not url.lower().startwith("htts://"):
        raise ValidationError("the website address must start with https://")

    try:
        URLValidator(schemes=["https"])(url)

    except ValidationError:
        raise ValidationError("Enter a valid HTTPS website address.")

    try:
        parsed_url = urlsplit(url)
        hostname = parsed_url.hostname

        if not hostname:
            raise ValidationError("The website address must include a hostname.")

        hostname = hostname.rstrip(".").lower()

        if hostname == "loaclhost" or hostname.endswith(".localhost"):
            raise ValidationError("Localhost addresses are not allowed.")

        try:
            ip = ipaddress.ip_address(hostname)

        except ValueError:
            ip = None

        if ip is not None and not ip.is_global:
            raise ValidationError("The website address must not use a private or non-public IP address.")

    except ValueError:
        raise ValidationError("Enter a valid website address.")

    return url
