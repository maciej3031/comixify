import os
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import load_img, img_to_array
from keras.applications.nasnet import preprocess_input
import tensorflow as tf
from PIL import Image

MODEL_PATH = 'neural_image_assessment/pretrained_model/nima_model.h5'


class NeuralImageAssessment:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            print("Model file does not exist.")
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = 0.001
        config.gpu_options.allow_growth = True
        self.session = tf.Session(config=config)
        with self.session.as_default():
            with tf.device('/CPU:0'):
                self.model = load_model(MODEL_PATH)

    @staticmethod
    def resize_image(bgr_img_array, target_size=(224, 224), interpolation='nearest'):
        _PIL_INTERPOLATION_METHODS = {
            'nearest': Image.NEAREST,
            'bilinear': Image.BILINEAR,
            'bicubic': Image.BICUBIC,
        }

        img = Image.fromarray(np.uint8(bgr_img_array[..., ::-1]))
        width_height_tuple = (target_size[1], target_size[0])
        if img.size != width_height_tuple:
            if interpolation not in _PIL_INTERPOLATION_METHODS:
                raise ValueError(
                    'Invalid interpolation method {} specified. Supported '
                    'methods are {}'.format(
                        interpolation,
                        ", ".join(_PIL_INTERPOLATION_METHODS.keys())))
            resample = _PIL_INTERPOLATION_METHODS[interpolation]
            img = img.resize(width_height_tuple, resample)
        return img

    def get_assessment_score(self, img_array):
        with self.session.as_default():
            target_size = (224, 224)
            img = NeuralImageAssessment.resize_image(img_array, target_size)
            x = img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)

            scores = self.model.predict(x, batch_size=1, verbose=0)[0]
        mean = NeuralImageAssessment.mean_score(scores)

        return mean

    @staticmethod
    def mean_score(scores):
        si = np.arange(1, 11, 1)
        mean = np.sum(scores * si)
        return mean

    @staticmethod
    def std_score(scores):
        si = np.arange(1, 11, 1)
        mean = NeuralImageAssessment.mean_score(scores)
        std = np.sqrt(np.sum(((si - mean) ** 2) * scores))
        return std
