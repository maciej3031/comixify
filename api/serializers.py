from django.conf import settings
from rest_framework import serializers

from .exceptions import FileExtensionError, TooLargeFile
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ("file", "timestamp")

    def validate(self, attrs):
        file = attrs.get("file")
        if file.name.split(".")[-1] not in settings.PERMITTED_VIDEO_EXTENSIONS:
            raise FileExtensionError
        if file.size > settings.MAX_FILE_SIZE:
            raise TooLargeFile
        return attrs
