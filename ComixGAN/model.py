import errno
import os

import tensorflow as tf
from django.conf import settings
from keras.models import load_model
from keras_contrib.layers import InstanceNormalization


class ComixGAN:
    def __init__(self):
        if not os.path.exists(settings.COMIX_GAN_MODEL_PATH):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), settings.COMIX_GAN_MODEL_PATH)
        self.graph = tf.Graph()
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.7
        config.gpu_options.allow_growth = True
        self.session = tf.Session(graph=self.graph, config=config)
        with self.graph.as_default():
            with self.session.as_default():
                with tf.device('/device:GPU:0'):
                    self.model = load_model(settings.COMIX_GAN_MODEL_PATH,
                                            custom_objects={'InstanceNormalization': InstanceNormalization})

