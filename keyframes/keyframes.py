import os
import shutil
import uuid
from subprocess import call

import cv2
from django.conf import settings

from utils import jj


class KeyFramesExtractor():
    @classmethod
    def get_keyframes(cls, video):
        all_keyframes, all_frames_tmp_dir = cls._get_all_frames(video)
        interval = cls._count_interval(all_keyframes)
        chosen_frames = cls._get_frames_with_interval(interval, all_keyframes)

        shutil.rmtree(jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}"))
        return chosen_frames

    @staticmethod
    def _get_all_frames(video):
        all_frames_tmp_dir = uuid.uuid4()
        os.mkdir(jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}"))
        call(["ffmpeg", "-skip_frame", "nokey", "-i", f"{video.file.path}", "-vsync", "0", "-qscale:v", "1",
              "-f", "image2", jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}", "%06d.jpeg")])

        frames_paths = []
        for dirname, dirnames, filenames in os.walk(jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}")):
            for filename in filenames:
                frames_paths.append(jj(dirname, filename))
        return sorted(frames_paths), all_frames_tmp_dir

    @staticmethod
    def _count_interval(all_keyframes):
        return int((len(all_keyframes) - settings.NUMBERS_OF_FRAMES_TO_SHOW) / (settings.NUMBERS_OF_FRAMES_TO_SHOW + 1))

    @staticmethod
    def _get_frames_with_interval(interval, all_keyframes):
        chosen_frames = []
        chosen_frames_tmp_dir = uuid.uuid4()
        os.mkdir(jj(f"{settings.TMP_DIR}", f"{chosen_frames_tmp_dir}"))

        for i in range(settings.NUMBERS_OF_FRAMES_TO_SHOW):
            frame = cv2.imread(all_keyframes[(i + 1) * interval])
            chosen_frames.append(frame)
        return chosen_frames
