from django.conf import settings
from rest_framework import serializers

from .exceptions import FileExtensionError, TooLargeFile


class VideoSerializer(serializers.Serializer):
    file = serializers.FileField()
    frames_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_FRAMES_SAMPLING_MODE)
    rl_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_RL_MODE)
    image_assessment_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_IMAGE_ASSESSMENT_MODE)

    def validate(self, attrs):
        file = attrs.get("file")
        if file.name.split(".")[-1] not in settings.PERMITTED_VIDEO_EXTENSIONS:
            raise FileExtensionError
        if file.size > settings.MAX_FILE_SIZE:
            raise TooLargeFile
        return attrs


class YouTubeDownloadSerializer(serializers.Serializer):
    url = serializers.URLField()
    frames_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_FRAMES_SAMPLING_MODE)
    rl_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_RL_MODE)
    image_assessment_mode = serializers.IntegerField(min_value=0, max_value=1, default=settings.DEFAULT_IMAGE_ASSESSMENT_MODE)
