# -*- coding: utf-8 -*-
"""UNet_ISIC17_Focalmodulation_Skip14_11_24.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1zeO_9yEbRS8J4gtE9h55Y46bRrdfbg8F
"""

from google.colab import drive
drive.mount('/content/drive')

# !pip uninstall tensorflow

!pip install keras==2.12.0

!pip install tensorflow==2.14.0

# Commented out IPython magic to ensure Python compatibility.
import os
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use("ggplot")
# %matplotlib inline

from tqdm import tqdm_notebook, tnrange
from itertools import chain
from skimage.io import imread, imshow, concatenate_images
from skimage.transform import resize
from skimage.morphology import label
from sklearn.model_selection import train_test_split

import tensorflow as tf

from keras.models import Model, load_model
from keras.layers import Input, BatchNormalization, Activation, Dense, Dropout
# from keras.layers.core import Lambda, RepeatVector, Reshape
# from keras.layers.convolutional import Conv2D, Conv2DTranspose
# from keras.layers.pooling import MaxPooling2D, GlobalMaxPool2D
# from keras.layers.merge import concatenate, add
from keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
# from keras.preprocessing.image import array_to_img, img_to_array, load_img
from tensorflow.keras.utils import img_to_array, array_to_img, load_img

import os
!cp '/content/drive/MyDrive/Segmentation_DSnet/ISIC2017_segmentation_data.zip' '/content/'
!unzip '/content/ISIC2017_segmentation_data.zip' -d '/content/' &> /dev/null
os.remove('/content/ISIC2017_segmentation_data.zip')

# Set some parameters
im_width = 256
im_height = 256
path_train = '/content/ISIC2017_segmentation_data'
# path_test = '../input/test/'

# Get and resize train images and masks
def get_data(path):
    images_paths = os.path.join(path,'images')
    masks_paths = os.path.join(path,'masks')

    images_ids = sorted(os.listdir(images_paths))
    masks_ids = sorted(os.listdir(masks_paths))

    X = np.zeros((len(images_ids), im_height, im_width, 3), dtype=np.float32)
    y = np.zeros((len(masks_ids), im_height, im_width, 1), dtype=np.float32)
    print('Getting and resizing images ... ')
    for n in range (len(images_ids)):
        # Load images

        img = load_img(os.path.join(images_paths,images_ids[n]), grayscale=False)
        x_img = img_to_array(img)
        x_img = resize(x_img, (im_height, im_width, 3), mode='constant', preserve_range=True)

        # Load masks

        mask = img_to_array(load_img(os.path.join(masks_paths,masks_ids[n]), grayscale=True))
        mask = resize(mask, (im_height, im_width, 1), mode='constant', preserve_range=True)

        # Save images
        X[n] = x_img / 255
        y[n] = mask / 255
    print('Done!')
    return X, y

X, y = get_data(path_train)

# Split train and valid
X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.20, random_state=2018)

# Commented out IPython magic to ensure Python compatibility.
from keras.models import *
from keras.layers import *
from keras.optimizers import *
from keras.callbacks import *
from keras.losses import *
# from keras import backend as keras
# from keras.applications.vgg16 import VGG16, preprocess_input
# from keras.applications.densenet import DenseNet201, DenseNet121
# from keras.utils.vis_utils import plot_model
# from keras.utils import plot_model
# from keras.preprocessing.image import ImageDataGenerator
import skimage.io as io
import skimage.transform as trans
import numpy as np
import glob
from PIL import Image
import skimage
from keras.initializers import Constant
from matplotlib import pyplot as plt
# %matplotlib inline
from skimage.morphology import disk
from sklearn.metrics import confusion_matrix
from skimage.measure import label, regionprops
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import jaccard_score

# def mean_squared_error(y_true, y_pred):
    # return K.mean(K.square(y_pred - y_true), axis=-1)

from keras import backend as K
def dice_coef(y_true, y_pred,smooth = 10):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_coef_loss(y_true, y_pred):
    return 1-dice_coef(y_true, y_pred)

def Jaccard_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (intersection ) / (K.sum(y_true_f) + K.sum(y_pred_f) - intersection)

def Jaccard_coef_loss(y_true, y_pred):
    return (1-Jaccard_coef(y_true, y_pred))

def bcc_dice_coef_loss(y_true, y_pred):
     return (binary_crossentropy(y_true, y_pred)+(dice_coef_loss(y_true, y_pred)))

# def bcc_Jaccard_coef_loss(y_true, y_pred):
#     return (binary_crossentropy(y_true, y_pred)+(1-Jaccard_coef(y_true, y_pred))+mean_squared_error(y_true, y_pred))



# from keras.layers.core import Lambda
# from keras.layers import *
# from keras.models import Model
# from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
# # from keras.preprocessing.image import ImageDataGenerator
# from keras.optimizers import *
# # from keras.utils import multi_gpu_model
# from matplotlib import pyplot as plt
# from keras.models import load_model
# import keras.backend as K
# import os

from tensorflow.keras import layers
def focal_modulation_block(inputs, gamma=2.0, alpha=0.25):
    # Get the number of channels in the input tensor
    num_channels = inputs.shape[-1]

    # Channel-wise mean calculation
    mean = layers.GlobalAveragePooling2D()(inputs)

    # Channel-wise max calculation
    max_val = layers.GlobalMaxPooling2D()(inputs)

    # Calculate the modulation factor for each channel
    modulation = (max_val - mean) * alpha

    # Apply the focal modulation to the input tensor
    modulation = layers.Reshape((1, 1, num_channels))(modulation)
    modulation = layers.Conv2D(filters=num_channels, kernel_size=1, activation='sigmoid')(modulation)

    # Scale the input tensor by the modulation factor
    scaled_inputs = layers.Multiply()([inputs, modulation])

    # Apply gamma power to the scaled inputs
    outputs = layers.Lambda(lambda x: x ** gamma)(scaled_inputs)

    return outputs

def focal_modulation_context_aggregation_block(inputs,filters):
    #After cancate the output will duble the filter and make it same for addition
    filters = int(filters)
    # Apply 2D convolution to capture local context
    conv1 = layers.Conv2D(filters, kernel_size=3, padding='same', activation='relu')(inputs)

    # Apply 2D convolution to capture global context
    conv2 = layers.Conv2D(filters, kernel_size=1, activation='relu')(inputs)
    global_context = layers.GlobalAveragePooling2D()(conv2)
    global_context = layers.Reshape((1, 1, filters))(global_context)
    global_context = layers.Conv2D(filters, kernel_size=1, activation='sigmoid')(global_context)
    global_context = layers.Multiply()([conv1, global_context])

    # Apply focal modulation block
    focal_modulation = focal_modulation_block(global_context)

    # Concatenate the local context and focal modulation output
    #concatenated = layers.Concatenate()([conv1, focal_modulation])
    add_features = add([conv1, focal_modulation])

    return add_features

def conv2d_block(input_tensor, n_filters, kernel_size=3, batchnorm=True):
    # first layer
    x = Conv2D(filters=n_filters, kernel_size=(kernel_size, kernel_size), kernel_initializer="he_normal",
               padding="same")(input_tensor)
    if batchnorm:
        x = BatchNormalization()(x)
    x = Activation("relu")(x)
    # second layer
    # x = Conv2D(filters=n_filters, kernel_size=(kernel_size, kernel_size), kernel_initializer="he_normal",
    #            padding="same")(x)
    # if batchnorm:
    #     x = BatchNormalization()(x)
    # x = Activation("relu")(x)
    return x

def get_unet(input_img, n_filters=16, dropout=0.5, batchnorm=True):
    # contracting path
    c1 = conv2d_block(input_img, n_filters=n_filters*1, kernel_size=3, batchnorm=batchnorm)
    p1 = MaxPooling2D((2, 2)) (c1)
    p1 = Dropout(dropout*0.5)(p1)

    c2 = conv2d_block(p1, n_filters=n_filters*2, kernel_size=3, batchnorm=batchnorm)
    p2 = MaxPooling2D((2, 2)) (c2)
    p2 = Dropout(dropout)(p2)

    c3 = conv2d_block(p2, n_filters=n_filters*4, kernel_size=3, batchnorm=batchnorm)
    p3 = MaxPooling2D((2, 2)) (c3)
    p3 = Dropout(dropout)(p3)

    c4 = conv2d_block(p3, n_filters=n_filters*8, kernel_size=3, batchnorm=batchnorm)
    p4 = MaxPooling2D(pool_size=(2, 2)) (c4)
    p4 = Dropout(dropout)(p4)
    c11 = focal_modulation_context_aggregation_block(c1,16)
    c22 = focal_modulation_context_aggregation_block(c2,32)
    c33 = focal_modulation_context_aggregation_block(c3,64)
    c44 = focal_modulation_context_aggregation_block(c4,128)
    c5 = conv2d_block(p4, n_filters=n_filters*16, kernel_size=3, batchnorm=batchnorm)
    att_layer=  focal_modulation_context_aggregation_block (c5, 128)

    # expansive path
    u6 = Conv2DTranspose(n_filters*8, (3, 3), strides=(2, 2), padding='same') (att_layer)
    u6 = concatenate([u6, c44])
    u6 = Dropout(dropout)(u6)
    c6 = conv2d_block(u6, n_filters=n_filters*8, kernel_size=3, batchnorm=batchnorm)

    u7 = Conv2DTranspose(n_filters*4, (3, 3), strides=(2, 2), padding='same') (c6)
    u7 = concatenate([u7, c33])
    u7 = Dropout(dropout)(u7)
    c7 = conv2d_block(u7, n_filters=n_filters*4, kernel_size=3, batchnorm=batchnorm)

    u8 = Conv2DTranspose(n_filters*2, (3, 3), strides=(2, 2), padding='same') (c7)
    u8 = concatenate([u8, c22])
    u8 = Dropout(dropout)(u8)
    c8 = conv2d_block(u8, n_filters=n_filters*2, kernel_size=3, batchnorm=batchnorm)

    u9 = Conv2DTranspose(n_filters*1, (3, 3), strides=(2, 2), padding='same') (c8)
    u9 = concatenate([u9, c11], axis=3)
    u9 = Dropout(dropout)(u9)
    c9 = conv2d_block(u9, n_filters=n_filters*1, kernel_size=3, batchnorm=batchnorm)

    outputs = Conv2D(1, (1, 1), activation='sigmoid') (c9)
    model = Model(inputs=[input_img], outputs=[outputs])
    return model

input_img = Input((im_height, im_width, 3), name='img')
model = get_unet(input_img, n_filters=16, dropout=0.05, batchnorm=True)
#  loss = bcct_Jaccard_coef_loss
model.compile(optimizer=Adam(learning_rate = 0.001), loss=bcc_dice_coef_loss, metrics=["accuracy"])
model.summary()

import tensorflow as tf
tf.keras.utils.plot_model(
    model,
    to_file='model.png',
    show_shapes=False,
    show_dtype=False,
    show_layer_names=True,
    rankdir='TB',
    expand_nested=False,
    dpi=96,
    layer_range=None,
    show_layer_activations=False,
    # show_trainable=False
)

from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
Earlystop = EarlyStopping(monitor='val_loss', mode='min',patience=9, min_delta=0.001)
anne = ReduceLROnPlateau(monitor='val_loss', factor=0.25, patience=4, verbose=1, min_lr=1e-9)
checkpoint = ModelCheckpoint('/content/drive/MyDrive/UNet_ISIC17_Focalmodulation_Skip14-11-24.h5', verbose=1, save_best_only=True,save_weights_only=True)
callbacks = [anne, checkpoint, Earlystop]

results = model.fit(X_train, y_train, batch_size=12, epochs=70, callbacks=callbacks,
                    validation_data=(X_valid, y_valid))



