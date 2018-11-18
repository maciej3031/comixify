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
        frames_mode = serializer.validated_data["frames_mode"]
        rl_mode = serializer.validated_data["rl_mode"]
        image_assessment_mode = serializer.validated_data["image_assessment_mode"]
        style_transfer_mode = serializer.validated_data["style_transfer_mode"]

        video = Video.objects.create(file=video_file)
        comix, timings = video.create_comix(
            yt_url='',
            frames_mode=frames_mode,
            rl_mode=rl_mode,
            image_assessment_mode=image_assessment_mode,
            style_transfer_mode=style_transfer_mode
        )

        response = {
            "status_message": "ok",
            "comic": comix.file.url,
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
        frames_mode = serializer.validated_data["frames_mode"]
        rl_mode = serializer.validated_data["rl_mode"]
        image_assessment_mode = serializer.validated_data["image_assessment_mode"]
        style_transfer_mode = serializer.validated_data["style_transfer_mode"]

        try:
            comix = Comic.objects.filter(yt_url=yt_url,
                                         frames_mode=frames_mode,
                                         rl_mode=rl_mode,
                                         image_assessment_mode=image_assessment_mode,
                                         style_transfer_mode=style_transfer_mode
                                         ).latest('timestamp')
            response = {
                "status_message": "ok",
                "comic": comix.file.url,
            }
        except Comic.DoesNotExist:
            video = Video()
            _, yt_download_time = video.download_from_youtube(yt_url)
            video.save()
            comix, timings = video.create_comix(
                yt_url=yt_url,
                frames_mode=frames_mode,
                rl_mode=rl_mode,
                image_assessment_mode=image_assessment_mode,
                style_transfer_mode=style_transfer_mode
            )

            timings['yt_download_time'] = yt_download_time
            response = {
                "status_message": "ok",
                "comic": comix.file.url,
                "timings": timings,
            }
            # Remove to spare storage
            video.file.delete()
        return Response(response)
