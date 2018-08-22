import cv2
import numpy as np


class LayoutGenerator():
    @classmethod
    def get_layout(cls, frames):
        result_imgs = cls._pad_images(frames)

        first_row = np.hstack(result_imgs[:2])
        second_row = np.hstack(result_imgs[2:5])
        third_row = np.hstack(result_imgs[5:7])
        fourth_row = np.hstack(result_imgs[7:10])

        second_row = cv2.resize(second_row,
                                (first_row.shape[1],
                                 (second_row.shape[0] * first_row.shape[1]) // second_row.shape[1]))
        fourth_row = cv2.resize(fourth_row,
                                (first_row.shape[1],
                                 (fourth_row.shape[0] * first_row.shape[1]) // fourth_row.shape[1]))

        return np.vstack([first_row, second_row, third_row, fourth_row])

    @staticmethod
    def _pad_images(frames):
        padded_result_imgs = []
        for img in frames:
            padded_img = cv2.copyMakeBorder(img, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(1, 1, 1))
            padded_result_imgs.append(padded_img)
        return padded_result_imgs
