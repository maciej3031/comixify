import os
import uuid

import cv2
from django.conf import settings
from django.core.files import File
from django.db import models


class Video(models.Model):
    file = models.FileField(blank=False, null=False, upload_to="raw_videos")
    timestamp = models.DateTimeField(auto_now_add=True)


class Comic(models.Model):
    file = models.FileField(blank=False, null=False, upload_to="comic")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comic")

    @classmethod
    def create_from_nparray(cls, nparray_file, video):
        if nparray_file.max() <= 1:
            nparray_file = (nparray_file * 255).astype(int)
        tmp_name = uuid.uuid4()
        cv2.imwrite(f"{settings.TMP_DIR}{tmp_name}.png", nparray_file)
        with open(f"{settings.TMP_DIR}{tmp_name}.png", mode="rb") as tmp_file:
            comic_image = File(tmp_file, name=f"{tmp_name}.png")
            comic = Comic.objects.create(file=comic_image, video=video)
        os.remove(f"{settings.TMP_DIR}{tmp_name}.png")
        return comic
