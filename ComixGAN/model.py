from keras import layers, Model
from keras_contrib.layers import InstanceNormalization


class ComixGAN():
    def __init__(self):
        # Build and compile the generator
        self.generator = self.build_generator()

    def build_generator(self):
        def residual_block(input_tensor):
            c1 = layers.Conv2D(256, (3, 3), strides=(1, 1), padding='same', use_bias=False)(input_tensor)
            bn1 = InstanceNormalization(axis=3)(c1)
            a1 = layers.Activation('relu')(bn1)
            c2 = layers.Conv2D(256, (3, 3), strides=(1, 1), padding='same', use_bias=False)(a1)
            bn2 = InstanceNormalization(axis=3)(c2)
            add1 = layers.add([bn2, input_tensor])

            return add1

        inp = layers.Input((None, None, 3))

        c1 = layers.Conv2D(64, (7, 7), strides=(1, 1), padding='same', use_bias=False)(inp)
        bn1 = InstanceNormalization(axis=3)(c1)
        a1 = layers.Activation('relu')(bn1)

        c2 = layers.Conv2D(128, (3, 3), strides=(2, 2), padding='same')(a1)
        c3 = layers.Conv2D(128, (3, 3), strides=(1, 1), padding='same', use_bias=False)(c2)
        bn2 = InstanceNormalization(axis=3)(c3)
        a2 = layers.Activation('relu')(bn2)

        c4 = layers.Conv2D(256, (3, 3), strides=(2, 2), padding='same')(a2)
        c5 = layers.Conv2D(256, (3, 3), strides=(1, 1), padding='same', use_bias=False)(c4)
        bn3 = InstanceNormalization(axis=3)(c5)
        a3 = layers.Activation('relu')(bn3)

        r1 = residual_block(a3)
        r2 = residual_block(r1)
        r3 = residual_block(r2)
        r4 = residual_block(r3)
        r5 = residual_block(r4)
        r6 = residual_block(r5)
        r7 = residual_block(r6)
        r8 = residual_block(r7)

        u1 = layers.UpSampling2D(size=(2, 2))(r8)
        c6 = layers.Conv2D(128, (3, 3), strides=(1, 1), padding='same', use_bias=False)(u1)
        bn4 = InstanceNormalization(axis=3)(c6)
        a4 = layers.Activation('relu')(bn4)

        u2 = layers.UpSampling2D(size=(2, 2))(a4)
        c7 = layers.Conv2D(64, (3, 3), strides=(1, 1), padding='same', use_bias=False)(u2)
        bn5 = InstanceNormalization(axis=3)(c7)
        a5 = layers.Activation('relu')(bn5)

        output = layers.Conv2D(3, (7, 7), strides=(1, 1), activation='sigmoid', padding='same')(a5)

        return Model(inputs=[inp], outputs=[output])


comixGAN = ComixGAN()
