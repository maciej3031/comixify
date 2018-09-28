import os
import uuid
import numpy as np
import torch
import torch.nn as nn
os.environ['GLOG_minloglevel'] = '2' # Prevent caffe shell loging
import caffe
from datetime import datetime
from subprocess import call
from math import ceil
from sklearn.preprocessing import normalize
from django.conf import settings
from django.core.cache import cache
from skimage import img_as_ubyte
import logging

from utils import jj
from keyframes_rl.models import DSN
from keyframes.kts import cpd_auto
from keyframes.utils import batch

logger = logging.getLogger(__name__)


class KeyFramesExtractor:
    @classmethod
    def get_keyframes(cls, video, gpu=settings.GPU, features_batch_size=settings.FEATURE_BATCH_SIZE):
        time = datetime.now()
        frames_paths, all_frames_tmp_dir = cls._get_all_frames(video)
        new_time = datetime.now()
        print("Extracted frames: " + str((time - new_time).seconds))
        time = new_time
        frames = cls._get_frames(frames_paths)
        new_time = datetime.now()
        print("Read frames: " + str((time - new_time).seconds))
        time = new_time
        features = cls._get_features(frames, gpu, features_batch_size)
        new_time = datetime.now()
        print("Extracted features: " + str((time - new_time).seconds))
        time = new_time
        change_points, frames_per_segment = cls._get_segments(features)
        new_time = datetime.now()
        print("Got segments: " + str((time - new_time).seconds))
        time = new_time
        probs = cls._get_probs(features, gpu)
        new_time = datetime.now()
        print("Got probs: " + str((time - new_time).seconds))
        chosen_frames = cls._get_chosen_frames(frames, probs, change_points, frames_per_segment)
        return chosen_frames

    @staticmethod
    def _get_all_frames(video):
        all_frames_tmp_dir = uuid.uuid4()
        os.mkdir(jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}"))
        call(["ffmpeg", "-i", f"{video.file.path}", "-vf", "select=not(mod(n\\,15))", "-vsync", "vfr", "-q:v", "2",
            jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}", "%06d.jpeg")])
        frames_paths = []
        for dirname, dirnames, filenames in os.walk(jj(f"{settings.TMP_DIR}", f"{all_frames_tmp_dir}")):
            for filename in filenames:
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
            print("Batch " + str(idx_batch) + " / " + str(n_batch))
            for i in range(n_batch):
                net.blobs['data'].data[i, ...] = transformer.preprocess("data", frames_batch[i])
            net.forward()
            temp = net.blobs["pool5/7x7_s1"].data[0:n_batch]
            temp = temp.squeeze().copy()
            features[idx_batch * batch_size:idx_batch * batch_size + n_batch] = temp
        normalize(features, copy=False)
        return features.astype(np.float32)
        
    @staticmethod
    def _get_probs(features, gpu=True):
        model_cache_key = "keyframes_rl_model_cache"
        model = cache.get(model_cache_key)  # get model from cache

        if model is None:
            model_path = "keyframes_rl/pretrained_model/model_epoch60.pth.tar"
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
    def _get_chosen_frames(frames, probs, change_points, frames_per_segment, min_keyframes=10):
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
                "frame": frames[x]
            })
        chosen_frames.sort(key=lambda k: k['index'])
        chosen_frames = [img_as_ubyte(o["frame"]) for o in chosen_frames]
        return chosen_frames

    @staticmethod
    def _get_segments(features):
        K = np.dot(features, features.T)
        n_frames = int(K.shape[0])
        min_segments = int(ceil(n_frames / 10))
        min_segments = max(10, min_segments)
        min_segments = min(n_frames - 1, min_segments)
        cps, scores = cpd_auto(K, min_segments, 1)
        change_points = [
            [0, cps[0] - 1]
        ]
        frames_per_segment = [int(cps[0])]
        for j in range(0, len(cps) - 1):
            change_points.append([cps[j], cps[j + 1] - 1])
            frames_per_segment.append(int(cps[j + 1] - cps[j]))
        frames_per_segment.append(int(len(features) - cps[len(cps) - 1]))
        change_points.append([cps[len(cps) - 1], len(features) - 1])
        return change_points, frames_per_segment
