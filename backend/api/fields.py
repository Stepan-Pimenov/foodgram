from io import BytesIO

from django.core.files.base import ContentFile
from drf_extra_fields.fields import Base64ImageField as ExtraBase64ImageField
from PIL import Image

MAX_IMAGE_SIDE = 1024


class Base64ImageField(ExtraBase64ImageField):
    """Base64-поле с уменьшением слишком большой картинки."""

    def to_internal_value(self, data):
        image_file = super().to_internal_value(data)
        return self.compress(image_file)

    def compress(self, image_file):
        image = Image.open(image_file)
        image_format = image.format or 'PNG'
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        buffer = BytesIO()
        image.save(buffer, format=image_format, optimize=True)
        return ContentFile(buffer.getvalue(), name=image_file.name)
