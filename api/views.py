from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from comic_layout.comic_layout import LayoutGenerator
from keyframes.keyframes import KeyFramesExtractor
from style_transfer.style_transfer import StyleTransfer
from .models import Video, Comic
from .serializers import VideoSerializer


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

        keyframes = KeyFramesExtractor.get_keyframes(video=video)
        stylized_keyframes = StyleTransfer.get_stylized_frames(frames=keyframes)
        comic_image = LayoutGenerator.get_layout(frames=stylized_keyframes)

        comic = Comic.create_from_nparray(comic_image, video)
        response = {
            "status_message": "ok",
            "comic": comic.file.url,
        }
        # Remove to spare storage
        video.file.delete()
        return Response(response)
