"""
This file contains the functions to generate the histogram of the selected image.
"""
import base64
import io
import os

import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

from app.config import Configuration

conf = Configuration()


def histogram_hub(image_id, histogram_type):
    """
    Receives from the HTML form the selected image, in the form of the ID, and the histogram type chosen by the user.
    The function calls the correct function to generate the desired histogram by passing the image_id.
    """
    match histogram_type:
        case "Mean":
            return mean_histogram(image_id)
        case "RGB":
            return RGB_histogram(image_id)


def mean_histogram(image_id):
    """
    Generates the mean histogram of the image.
    """
    image_path = os.path.join(conf.image_folder_path, image_id)
    # Open the image
    im = Image.open(image_path)
    im_array = np.array(im)
    # Calculate the mean pixel value across RGB channels
    vals = im_array.mean(axis=2).flatten()
    # Create the histogram
    counts, bins = np.histogram(vals, range(257))
    plt.bar(bins[:-1] - 0.5, counts, width=1, edgecolor='none')
    plt.xlim([-0.5, 255.5])

    # Histogram captions
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Count')
    # encode histogram as base64
    tmpfile = io.BytesIO()
    plt.savefig(tmpfile, format='png')
    plt.close()
    tmpfile.seek(0)

    plot = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return plot


def RGB_histogram(image_id):
    """
    Generates a histogram which plots the pixel intensities of the RGB channels separated.
    Plots in red the intensity of the red channel, same goes for green and blue.
    """
    image_path = os.path.join(conf.image_folder_path, image_id)
    im = cv2.imread(image_path)
    histSize = 256
    histRange = (0, histSize)

    # Converts the image from BGR color space to RGB color space
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

    # Plotting the histogram
    color = ('b', 'g', 'r')
    plt.figure()
    for i, col in enumerate(color):
        histr = cv2.calcHist([rgb], [i], None, [256], [0, 256])
        plt.plot(histr, color=col)
        plt.xlim([0, 256])

    # Histogram captions
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Count')
    # encode histogram as base64
    tmpfile = io.BytesIO()
    plt.savefig(tmpfile, format='png')
    plt.close()
    tmpfile.seek(0)

    plot = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    return plot
