from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Video, Comic
from .serializers import VideoSerializer, YouTubeDownloadSerializer


class Comixify(APIView):
    parser_classes = (FormParser, MultiPartParser)

    def post(self, request):
        """
        Receives video, and returns comic image
        """

        serializer = VideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_file = serializer.validated_data["file"]
        video = Video.objects.create(file=video_file)
        comic_image, timings = video.create_comic(
            frames_mode=serializer.validated_data["frames_mode"],
            rl_mode=serializer.validated_data["rl_mode"],
            image_assessment_mode=serializer.validated_data["image_assessment_mode"],
            style_transfer_mode=serializer.validated_data["rl_mode"],
        )
        comic, from_nparray_time = Comic.create_from_nparray(comic_image, video)
        timings['from_nparray_time'] = from_nparray_time

        response = {
            "status_message": "ok",
            "comic": comic.file.url,
            "timings": timings,
        }
        # Remove to spare storage
        video.file.delete()
        return Response(response)


class ComixifyFromYoutube(APIView):

    def post(self, request):
        """
        Receives video, and returns comic image
        """

        serializer = YouTubeDownloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        yt_url = serializer.validated_data["url"]

        video = Video()
        _, yt_download_time = video.download_from_youtube(yt_url)
        video.save()
        comic_image, timings = video.create_comic(
            frames_mode=serializer.validated_data["frames_mode"],
            rl_mode=serializer.validated_data["rl_mode"],
            image_assessment_mode=serializer.validated_data["image_assessment_mode"],
            style_transfer_mode=serializer.validated_data["rl_mode"],
        )
        comic, from_nparray_time = Comic.create_from_nparray(comic_image, video)
        timings['from_nparray_time'] = from_nparray_time
        timings['yt_download_time'] = yt_download_time

        response = {
            "status_message": "ok",
            "comic": comic.file.url,
            "timings": timings,
        }
        # Remove to spare storage
        video.file.delete()
        return Response(response)
