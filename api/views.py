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
        comic_image = video.create_comic()
        comic = Comic.create_from_nparray(comic_image, video)

        response = {
            "status_message": "ok",
            "comic": comic.file.url,
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
        video.download_from_youtube(yt_url)
        video.save()
        comic_image = video.create_comic()
        comic = Comic.create_from_nparray(comic_image, video)

        response = {
            "status_message": "ok",
            "comic": comic.file.url,
        }
        # Remove to spare storage
        video.file.delete()
        return Response(response)
