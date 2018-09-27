from django.test import TestCase

import numpy as np
from keyframes.keyframes import KeyFramesExtractor
from api.models import Video
from django.core.files import File
import shutil
from utils import jj
from django.conf import settings
from keyframes.utils import batch

VIDEO_PATH = "tmp/f1_short.mp4" 
VIDEO_N_FRAMES = 47 


class KeyframesTestCase(TestCase):

    def setUp(self):
        f = open(VIDEO_PATH, 'rb')
        self.video = Video.objects.create(file=File(f))

    def tearDown(self):
        shutil.rmtree(jj(f"{settings.TMP_DIR}", f"{self.all_frames_tmp_dir}"))

    def test_keyframes(self):
        """Keyframes are extracted corectly"""

        frames_paths, all_frames_tmp_dir = KeyFramesExtractor._get_all_frames(self.video)
        self.assertIsInstance(frames_paths[0], str)
        self.assertEqual(len(frames_paths), VIDEO_N_FRAMES)
        self.all_frames_tmp_dir = all_frames_tmp_dir

        frames = KeyFramesExtractor._get_frames(frames_paths)
        self.assertEqual(len(frames), VIDEO_N_FRAMES)
        self.assertIsInstance(frames[0], np.ndarray)

        features = KeyFramesExtractor._get_features(frames, False)
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape, (VIDEO_N_FRAMES, 1024))

        change_points, frames_per_segment = KeyFramesExtractor._get_segments(features)
        self.assertIsInstance(change_points, list)
        self.assertIsInstance(frames_per_segment, list)

        for cp in frames_per_segment:
            with self.subTest(cp=cp):
                self.assertIsInstance(cp, int)

        probs = KeyFramesExtractor._get_probs(features, False)
        self.assertIsInstance(probs, np.ndarray)
        self.assertEqual(probs.shape, (VIDEO_N_FRAMES, ))

        chosen_frames = KeyFramesExtractor._get_chosen_frames(frames, probs, change_points, frames_per_segment)
        self.assertIsInstance(chosen_frames, list)
        self.assertTrue(len(chosen_frames) == 10)


class UtilsTestCase(TestCase):
    def test_batch(self):
        """Barch is working"""
        arr = [1, 1, 2, 2, 3, 3, 4]
        batched_arr = batch(arr, 2)
        self.assertEqual(list(batched_arr), [(2, [1, 1]), (2, [2, 2]), (2, [3, 3]), (1, [4])])

    def test_empty_batch(self):
        """Barch is working"""
        arr = []
        batched_arr = batch(arr, 2)
        self.assertEqual(list(batched_arr), [])
