import os

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from django.conf import settings
from django.core.cache import cache
from keras.models import load_model
from torch.autograd import Variable

from CartoonGAN.network.Transformer import Transformer
from utils import profile
from ComixGAN.model import ComixGAN


class StyleTransfer():
    @classmethod
    @profile
    def get_stylized_frames(cls, frames, style_transfer_mode=0, gpu=settings.GPU):
        if style_transfer_mode == 0:
            return cls._comix_gan_stylize(frames=frames)
        elif style_transfer_mode == 1:
            return cls._cartoon_gan_stylize(frames, gpu=gpu, style='Hayao')
        elif style_transfer_mode == 2:
            return cls._cartoon_gan_stylize(frames, gpu=gpu, style='Hosoda')

    @staticmethod
    def _resize_images(frames, size=384):
        resized_images = []
        for img in frames:
            # resize image, keep aspect ratio
            h, w, _ = img.shape
            ratio = h / w
            if ratio > 1:
                h = size
                w = int(h * 1.0 / ratio)
            else:
                w = size
                h = int(w * ratio)
            resized_img = cv2.resize(img, (w, h))
            resized_images.append(resized_img)
            return resized_images

    @classmethod
    def _comix_gan_stylize(cls, frames):
        comixGAN_cache_key = 'comixGAN_model_cache'
        comixGAN_model = cache.get(comixGAN_cache_key)  # get model from cache

        if comixGAN_model is None:
            # load pretrained model
            comixGAN_model = ComixGAN()
            comixGAN_model.generator = load_model(settings.COMIX_GAN_MODEL_PATH)
            cache.set(comixGAN_cache_key, comixGAN_model, None)  # None is the timeout parameter. It means cache forever

        frames = cls._resize_images(frames, size=384)
        frames = np.stack(frames)
        frames = frames / 255
        stylized_imgs = comixGAN_model.generator.predict(frames)
        return list(255 * stylized_imgs)

    @classmethod
    def _cartoon_gan_stylize(cls, frames, gpu=True, style='Hayao'):
        model_cache_key = 'model_cache'
        model = cache.get(model_cache_key)  # get model from cache

        if model is None:
            # load pretrained model
            model = Transformer()
            model.load_state_dict(torch.load(os.path.join("CartoonGAN/pretrained_model", style + "_net_G_float.pth")))
            model.eval()
            model.cuda() if gpu else model.float()
            cache.set(model_cache_key, model, None)  # None is the timeout parameter. It means cache forever

        frames = cls._resize_images(frames, size=450)
        stylized_imgs = []
        for img in frames:
            input_image = transforms.ToTensor()(img).unsqueeze(0)

            # preprocess, (-1, 1)
            input_image = -1 + 2 * input_image
            input_image = Variable(input_image).cuda() if gpu else Variable(input_image).float()

            # forward
            output_image = model(input_image)
            output_image = output_image[0]

            # deprocess, (0, 1)
            output_image = (output_image.data.cpu().float() * 0.5 + 0.5).numpy()

            # switch channels -> (c, h, w) -> (h, w, c)
            output_image = np.rollaxis(output_image, 0, 3)

            # append image to result images
            stylized_imgs.append(255 * output_image)

        return stylized_imgs
