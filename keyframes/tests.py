from django.test import TestCase

import numpy as np
from keyframes.keyframes import KeyFramesExtractor
from api.models import Video
from django.core.files import File
import shutil
from utils import jj
from django.conf import settings


class KeyframesTestCase(TestCase):

    def setUp(self):
        video_file = "tmp/f1.mp4"
        f = open(video_file, 'rb')
        self.video = Video.objects.create(file=File(f))

    def tearDown(self):
        shutil.rmtree(jj(f"{settings.TMP_DIR}", f"{self.all_frames_tmp_dir}"))

    def test_keyframes(self):
        """Keyframes are extracted corectly"""
        
        frames_paths, all_frames_tmp_dir = KeyFramesExtractor._get_all_frames(self.video)
        self.assertIsInstance(frames_paths[0], str)
        self.assertEqual(len(frames_paths), 193)
        self.all_frames_tmp_dir = all_frames_tmp_dir

        frames = KeyFramesExtractor._get_frames(frames_paths)
        self.assertEqual(len(frames), 193)
        self.assertIsInstance(frames[0], np.ndarray)

        # features = KeyFramesExtractor._get_features(frames, False)
        # segments = KeyFramesExtractor._get_segments(features)
        # probs = KeyFramesExtractor._get_probs(features, False)
        # chosen_frames = KeyFramesExtractor._get_chosen_frames(frames, probs)


    