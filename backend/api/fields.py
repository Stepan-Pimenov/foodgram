import base64
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers

MAX_IMAGE_SIDE = 1024


class Base64ImageField(serializers.ImageField):
    """Поле картинки: принимает base64 и сжимает картинку."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = header.split('/')[-1]
            data = ContentFile(
                self.compress(base64.b64decode(imgstr)),
                name=f'temp.{ext}',
            )
        return super().to_internal_value(data)

    def compress(self, raw):
        image = Image.open(BytesIO(raw))
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        buffer = BytesIO()
        image.save(buffer, format=image.format or 'PNG', optimize=True)
        return buffer.getvalue()
