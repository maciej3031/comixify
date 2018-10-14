import pickle

MODEL_PATH = 'popularity/pretrained_model/svr_test_11.10.sk'


class PopularityPredictor:
    def __init__(self):
        with open(MODEL_PATH, 'rb') as fp:
            self.svr = pickle.load(fp, encoding='latin1')

    def get_popularity_score(self, image_feature):
        image_feature = image_feature.reshape(1, -1)
        return self.svr.predict(image_feature)
