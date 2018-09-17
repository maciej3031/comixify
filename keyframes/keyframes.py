import os
from subprocess import call
import shutil
import uuid
import cv2
import argparse
import sys
import time
import datetime
import numpy as np
import torch
from django.conf import settings
import caffe
import operator
from math import ceil, floor

from utils import jj
from keyframes_rl.models import DSN
from keyframes_rl.knapsack import knapsack_dp
from keyframes.kts import cpd_auto

class KeyFramesExtractor():
    @classmethod
    def get_keyframes(cls, video, gpu=settings.GPU):
        frames_paths, all_frames_tmp_dir = cls._get_all_frames(video)
        frames = cls._get_frames(frames_paths)
        features = cls._get_features(frames, gpu)
        segments = cls._get_segments(features)
        probs = cls._get_probs(features, gpu)
        chosen_frames = cls._get_chosen_frames(frames, probs)
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
            frame = cv2.imread(frame_path)
            frames.append(frame)
        return frames

    @staticmethod
    def _get_features(frames, gpu=True):
        caffe_root = os.environ.get("CAFFE_ROOT")
        if not caffe_root:
            print("Caffe root path not found.")

        MODEL_FILE = caffe_root + "models/bvlc_googlenet/deploy.prototxt"
        PRETRAINED = caffe_root + "models/bvlc_googlenet/bvlc_googlenet.caffemodel"

        if not os.path.isfile(PRETRAINED):
            print("PRETRAINED Model not found.")
        if not gpu:
            caffe.set_mode_cpu()
        net = caffe.Net(MODEL_FILE, PRETRAINED, caffe.TEST)

        # resize input size as we have only one image per batch.
        net.blobs["data"].reshape(1, 3, 224, 224)

        mu = np.load(caffe_root + "python/caffe/imagenet/ilsvrc_2012_mean.npy")
        mu = mu.mean(1).mean(1)  # average over pixels to obtain the mean (BGR) pixel values
        
        # create transformer for the input called "data"
        transformer = caffe.io.Transformer({"data": net.blobs["data"].data.shape})

        transformer.set_transpose("data", (2,0,1))      # move image channels to outermost dimension
        transformer.set_mean("data", mu)                # subtract the dataset-mean value in each channel
        transformer.set_raw_scale("data", 255)          # rescale from [0, 1] to [0, 255]
        transformer.set_channel_swap("data", (2,1,0))   # swap channels from RGB to BGR

        features = []
        for frame in frames:
            transformed_image = transformer.preprocess("data", frame)
            net.blobs["data"].data[0] = transformed_image 
            net.forward()
            # features from pool5 layer
            temp = net.blobs["pool5/7x7_s1"].data[0] 
            temp = temp.squeeze()
            temp *= 0.03661728635813100419730620095037 # temprorary normalisation constant
            features.append(temp)
        features = np.array(features)
        return features
        
    @staticmethod
    def _get_probs(features, gpu=True):
        model = DSN(in_dim=1024, hid_dim=256, num_layers=1, cell="lstm")
        checkpoint = torch.load("keyframes_rl/pretrained_model/summe1.pth.tar")
        model.load_state_dict(checkpoint)
        if gpu:
            model = nn.DataParallel(model).cuda()
        model.eval()
        seq = torch.from_numpy(features).unsqueeze(0)
        if gpu: seq = seq.cuda()
        probs = model(seq)
        probs = probs.data.cpu().squeeze().numpy()
        return probs

    @staticmethod
    def _get_chosen_frames(frames, probs, segments):
        n_frames = len(frames)
        frames_per_segment = [int(segments[0])]
        for j in range(0, len(segments) - 1):
            frames_per_segment.append(int(segments[j + 1] - segments[j]))
        frames_per_segment.append(int(n_frames - segments[len(segments) - 1]))
        capacity = int(int(n_frames) * 0.55)
        picks = knapsack_dp(probs, frames_per_segment, n_frames, capacity)
        chosen_frames = []
        for pick in picks:
            cp = segments[pick]
            low = cp[0]
            high = cp[1]
            x = low + np.argmax(gtscore[low:high])
            chosen_frames.append(frames[x])
        return chosen_frames

    @staticmethod
    def _get_segments(features):
        K = np.dot(features, features.T)
        cps, scores = cpd_auto(K, math.ceil(K.shape[0] / 10), 1)
        return cps
    