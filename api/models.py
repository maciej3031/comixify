import os
import uuid

import cv2
import pafy
from django.conf import settings
from django.core.files import File
from django.db import models

from api.exceptions import TooLargeFile
from comic_layout.comic_layout import LayoutGenerator
from keyframes.keyframes import KeyFramesExtractor
from style_transfer.style_transfer import StyleTransfer
from utils import jj


class Video(models.Model):
    file = models.FileField(blank=False, null=False, upload_to="raw_videos")
    timestamp = models.DateTimeField(auto_now_add=True)

    def download_from_youtube(self, yt_url):
        yt_pafy = pafy.new(yt_url)

        # Use the biggest possible quality with file size < MAX_FILE_SIZE and resolution <= 480px
        for stream in yt_pafy.videostreams:
            if stream.get_filesize() < settings.MAX_FILE_SIZE and int(stream.quality.split("x")[1]) <= 480:
                tmp_name = uuid.uuid4().hex + ".mp4"
                relative_path = jj('raw_videos', tmp_name)
                full_path = jj(settings.MEDIA_ROOT, relative_path)
                stream.download(full_path)
                self.file.name = relative_path
                break
        else:
            raise TooLargeFile()

    def create_comic(self):
        keyframes = KeyFramesExtractor.get_keyframes(video=self)
        stylized_keyframes = StyleTransfer.get_stylized_frames(frames=keyframes)
        comic_image = LayoutGenerator.get_layout(frames=stylized_keyframes)
        return comic_image


class Comic(models.Model):
    file = models.FileField(blank=False, null=False, upload_to="comic")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comic")

    @classmethod
    def create_from_nparray(cls, nparray_file, video):
        if nparray_file.max() <= 1:
            nparray_file = (nparray_file * 255).astype(int)
        tmp_name = uuid.uuid4().hex + ".png"
        cv2.imwrite(jj(settings.TMP_DIR, tmp_name), nparray_file)
        with open(jj(settings.TMP_DIR, tmp_name), mode="rb") as tmp_file:
            comic_image = File(tmp_file, name=tmp_name)
            comic = Comic.objects.create(file=comic_image, video=video)
        os.remove(jj(settings.TMP_DIR, tmp_name))
        return comic
