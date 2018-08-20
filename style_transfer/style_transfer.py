import os

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from django.conf import settings
from torch.autograd import Variable

from CartoonGAN.network.Transformer import Transformer


class StyleTransfer():
    @classmethod
    def get_stylized_frames(cls, frames, method="cartoon_gan", gpu=settings.GPU, **kwargs):
        if method == "cartoon_gan":
            return cls._cartoon_gan_stylize(frames, gpu=gpu, **kwargs)

    @staticmethod
    def _cartoon_gan_stylize(frames, gpu=True, **kwargs):
        style = kwargs.get("style", "Hosoda")
        resize = kwargs.get("resize", 450)

        # load pretrained model
        model = Transformer()
        model.load_state_dict(torch.load(os.path.join("CartoonGAN/pretrained_model", style + "_net_G_float.pth")))
        model.eval()
        model.cuda() if gpu else model.float()

        stylized_imgs = []
        for img in frames:
            # resize image, keep aspect ratio
            h, w, _ = img.shape
            ratio = h * 1.0 / w
            if ratio > 1:
                h = resize
                w = int(h * 1.0 / ratio)
            else:
                w = resize
                h = int(w * ratio)
            input_image = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

            # RGB -> BGR
            input_image = input_image[:, :, [2, 1, 0]]
            input_image = transforms.ToTensor()(input_image).unsqueeze(0)

            # preprocess, (-1, 1)
            input_image = -1 + 2 * input_image
            input_image = Variable(input_image).cuda() if gpu else Variable(input_image).float()

            # forward
            output_image = model(input_image)
            output_image = output_image[0]

            # BGR -> RGB
            output_image = output_image[[2, 1, 0], :, :]

            # deprocess, (0, 1)
            output_image = output_image.data.cpu().float() * 0.5 + 0.5

            # switch channels and append image to result images
            stylized_imgs.append(np.rollaxis(output_image.numpy(), 0, 3))

        return stylized_imgs
