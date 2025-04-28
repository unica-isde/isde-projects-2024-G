"""This function generates the mean histogram of the selected image."""
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
    match histogram_type:
        case "Mean":
            return mean_histogram(image_id)
        case "RGB":
            return RGB_histogram(image_id)


def mean_histogram(image_id):
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
    image_path = os.path.join(conf.image_folder_path, image_id)
    im = cv2.imread(image_path)
    histSize = 256
    histRange = (0, histSize)
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    # calcHist
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
