import os
import uuid

import numpy as np
import torch
import torch.nn as nn

os.environ['GLOG_minloglevel'] = '2'  # Prevent caffe shell loging
import caffe
from subprocess import call
from math import ceil
from sklearn.preprocessing import normalize
from django.conf import settings
from django.core.cache import cache
from skimage import img_as_ubyte
import logging

from utils import jj, profile
from keyframes_rl.models import DSN
from popularity.models import PopularityPredictor
from neural_image_assessment.models import NeuralImageAssessment
from keyframes.kts import cpd_auto
from keyframes.utils import batch

logger = logging.getLogger(__name__)

nima_model = NeuralImageAssessment()


class KeyFramesExtractor:
    @classmethod
    @profile
    def get_keyframes(cls, video, gpu=settings.GPU, features_batch_size=settings.FEATURE_BATCH_SIZE,
                      frames_mode=0, rl_mode=0, image_assessment_mode=0):
        frames_paths, all_frames_tmp_dir = cls._get_all_frames(video, mode=frames_mode)
        frames = cls._get_frames(frames_paths)
        features = cls._get_features(frames, gpu, features_batch_size)
        norm_features = normalize(features)
        change_points, frames_per_segment = cls._get_segments(norm_features)
        probs = cls._get_probs(norm_features, gpu, mode=rl_mode)
        keyframes = cls._get_keyframes(frames, probs, change_points, frames_per_segment)
        chosen_frames = cls._get_popularity_chosen_frames(keyframes, features, image_assessment_mode)
        return chosen_frames

    @staticmethod
    def _get_all_frames(video, mode=0):
        all_frames_tmp_dir = uuid.uuid4().hex
        os.mkdir(jj(settings.TMP_DIR, all_frames_tmp_dir))
        if mode == 1:
            call(["ffmpeg", "-i", f"{video.file.path}", "-c:v", "libxvid", "-qscale:v", "1", "-an",
                  jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}", "video.mp4")])
            call(["ffmpeg", "-i", jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}", "video.mp4"), "-vf",
                  "select=eq(pict_type\,I)", "-vsync", "vfr",
                  jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}", "%06d.jpeg")])
        else:
            call(["ffmpeg", "-i", video.file.path, "-vf", "select=not(mod(n\\,15))", "-vsync", "vfr", "-q:v", "2",
                  jj(settings.TMP_DIR, all_frames_tmp_dir, "%06d.jpeg")])
        frames_paths = []
        for dirname, dirnames, filenames in os.walk(jj(settings.TMP_DIR, all_frames_tmp_dir)):
            for filename in filenames:
                if not filename.endswith(".mp4"):
                    frames_paths.append(jj(dirname, filename))
        return sorted(frames_paths), all_frames_tmp_dir

    @staticmethod
    def _get_frames(frames_paths):
        frames = []
        for frame_path in frames_paths:
            frame = caffe.io.load_image(frame_path)
            frames.append(frame)
        return frames

    @staticmethod
    def _get_features(frames, gpu=True, batch_size=1):
        caffe_root = os.environ.get("CAFFE_ROOT")
        if not caffe_root:
            print("Caffe root path not found.")
        if not gpu:
            caffe.set_mode_cpu()
        else:
            caffe.set_mode_gpu()

        model_file = caffe_root + "/models/bvlc_googlenet/deploy.prototxt"
        pretrained = caffe_root + "/models/bvlc_googlenet/bvlc_googlenet.caffemodel"
        if not os.path.isfile(pretrained):
            print("PRETRAINED Model not found.")

        net = caffe.Net(model_file, pretrained, caffe.TEST)
        net.blobs["data"].reshape(batch_size, 3, 224, 224)

        mu = np.load(caffe_root + "/python/caffe/imagenet/ilsvrc_2012_mean.npy")
        mu = mu.mean(1).mean(1)
        transformer = caffe.io.Transformer({"data": net.blobs["data"].data.shape})
        transformer.set_transpose("data", (2, 0, 1))
        transformer.set_mean("data", mu)
        transformer.set_raw_scale("data", 255)
        transformer.set_channel_swap("data", (2, 1, 0))

        features = np.zeros(shape=(len(frames), 1024))
        for idx_batch, (n_batch, frames_batch) in enumerate(batch(frames, batch_size)):
            for i in range(n_batch):
                net.blobs['data'].data[i, ...] = transformer.preprocess("data", frames_batch[i])
            net.forward()
            temp = net.blobs["pool5/7x7_s1"].data[0:n_batch]
            temp = temp.squeeze().copy()
            features[idx_batch * batch_size:idx_batch * batch_size + n_batch] = temp
        return features.astype(np.float32)

    @staticmethod
    def _get_probs(features, gpu=True, mode=0):
        model_cache_key = "keyframes_rl_model_cache_" + str(mode)
        model = cache.get(model_cache_key)  # get model from cache

        if model is None:
            if mode == 1:
                model_path = "keyframes_rl/pretrained_model/model_1.pth.tar"
            else:
                model_path = "keyframes_rl/pretrained_model/model_0.pth.tar"
            model = DSN(in_dim=1024, hid_dim=256, num_layers=1, cell="lstm")
            if gpu:
                checkpoint = torch.load(model_path)
            else:
                checkpoint = torch.load(model_path, map_location='cpu')
            model.load_state_dict(checkpoint)
            if gpu:
                model = nn.DataParallel(model).cuda()
            model.eval()
            cache.set(model_cache_key, model, None)

        seq = torch.from_numpy(features).unsqueeze(0)
        if gpu: seq = seq.cuda()
        probs = model(seq)
        probs = probs.data.cpu().squeeze().numpy()
        return probs

    @staticmethod
    def _get_keyframes(frames, probs, change_points, frames_per_segment, min_keyframes=20):
        gts = []
        s = 0
        for q in frames_per_segment:
            gts.append(np.mean(probs[s:s + q]).astype(float))
            s += q
        gts = np.array(gts)
        picks = np.argsort(gts)[::-1][:min_keyframes]
        chosen_frames = []
        for pick in picks:
            cp = change_points[pick]
            low = cp[0]
            high = cp[1]
            x = low
            if low != high:
                x = low + np.argmax(probs[low:high])
            chosen_frames.append({
                "index": x,
                "frame": img_as_ubyte(frames[x])[..., ::-1]
            })
        chosen_frames.sort(key=lambda k: k['index'])
        return chosen_frames

    @staticmethod
    def _get_popularity_chosen_frames(frames, features, image_assessment_mode=0, n_frames=10):
        if image_assessment_mode == 1:
            model_cache_key = "popularity_model_cache"
            model = cache.get(model_cache_key)  # get model from cache
            if model is None:
                model = PopularityPredictor()
                cache.set(model_cache_key, model, None)
            for frame in frames:
                x = features[frame["index"]]
                frame["popularity"] = model.get_popularity_score(x).squeeze()
        else:
            for frame in frames:
                x = frame["frame"]
                frame["popularity"] = nima_model.get_assessment_score(x)
        chosen_frames = sorted(frames, key=lambda k: k['popularity'], reverse=True)
        chosen_frames = chosen_frames[0:n_frames]
        chosen_frames.sort(key=lambda k: k['index'])
        return [o["frame"] for o in chosen_frames]

    @staticmethod
    def _get_segments(features):
        K = np.dot(features, features.T)
        n_frames = int(K.shape[0])
        min_segments = int(ceil(n_frames / 20))
        min_segments = max(20, min_segments)
        min_segments = min(n_frames - 1, min_segments)
        cps, scores = cpd_auto(K, min_segments, 1, min_segments=min_segments)
        change_points = [
            [0, cps[0] - 1]
        ]
        frames_per_segment = [int(cps[0])]
        for j in range(0, len(cps) - 1):
            change_points.append([cps[j], cps[j + 1] - 1])
            frames_per_segment.append(int(cps[j + 1] - cps[j]))
        frames_per_segment.append(int(len(features) - cps[len(cps) - 1]))
        change_points.append([cps[len(cps) - 1], len(features) - 1])
        print("Number of segments: " + str(len(frames_per_segment)))
        return change_points, frames_per_segment
