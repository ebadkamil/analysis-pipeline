"""
Analysis and visualization
Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy import ndimage as ndi

from skimage import feature


class EdgeDetection(object):
    def __init__(self, sigma=3, apply_filter=True):
        self._sigma = sigma
        self._apply_filter = apply_filter
        self.edges = None

    def find_edges(self, image):
        if self._apply_filter:
            image = ndi.gaussian_filter(image, 4)

        def _find_edge(i):
            edges = feature.canny(image[i], sigma=self._sigma)
            return edges

        with ThreadPoolExecutor(max_workers=10) as executor:
            ret = executor.map(_find_edge, range(image.shape[0]))

        self.edges = np.stack(ret)
        return self.edges
