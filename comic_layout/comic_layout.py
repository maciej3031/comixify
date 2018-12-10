import cv2
import numpy as np

from utils import profile


class LayoutGenerator():

    @classmethod
    def _gen_image_row(cls, images, width):
        image_row = np.hstack(images)
        if image_row.shape[1] != width:
            nominal_height = image_row.shape[0]
            image_row = cv2.resize(
                image_row,
                (width, (nominal_height * width) // nominal_height)
            )
        return image_row

    @classmethod
    def _get_row_layout(cls, scores):
        return [2, 3, 1, 3, 1]

    @classmethod
    @profile
    def get_layout(cls, frames, scores):
        result_images = cls._pad_images(frames)
        row_layout = cls._get_row_layout(scores)
        width = result_images[0].shape[1]

        index = 0
        rows = []
        for row_length in row_layout:
            row = cls._gen_image_row(result_images[index:index + row_length], width)
            rows.append(row)
            index += row_length

        return np.vstack(rows)

    @staticmethod
    def _pad_images(frames):
        padded_result_images = []
        for img in frames:
            padded_img = cv2.copyMakeBorder(img, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(255, 255, 255))
            padded_result_images.append(padded_img)
        return padded_result_images
