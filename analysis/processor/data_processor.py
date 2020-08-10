"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""

from datetime import datetime
import multiprocessing as mp
import queue

import numpy as np

from .azimuthal_integration import ImageIntegrator


class DataProcessor(mp.Process):
    def __init__(self, data_in, data_out):
        super().__init__()

        self._data_in = data_in
        self._data_out = data_out
        self._running = False

        self.integrator = ImageIntegrator()

    def run(self):
        self._running = True

        while self._running:
            try:
                raw = self._data_in.get_nowait()
            except queue.Empty:
                continue

            mean_image, momentum, intensities = self.process(raw)

            proc_data = IntegratedData(raw[0]['timestamp'])
            proc_data.mean_image = mean_image
            proc_data.momentum = momentum
            proc_data.intensities = intensities

            while self._running:
                try:
                    self._data_out.put_nowait(proc_data)
                    break
                except queue.Full:
                    continue

    def process(self, raw):
        meta, data = raw
        config = dict(energy=9.3,
                      pixel_size=0.5e-3,
                      centrex=512,
                      centrey=512,
                      distance=0.2,
                      intg_rng=[0., 5],
                      intg_method='BBox',
                      intg_pts=1024,
                      threshold_mask=(0,12),
                      user_mask=None)

        image = data['image']
        mom, intensities = self.integrator.integrate(config, image)
        return np.mean(image, axis=0), mom, intensities


class IntegratedData:
    def __init__(self, timestamp):
        self._timestamp = timestamp
        self.mean_image = None
        self.momentum = None
        self.intensities = None

    @property
    def timestamp(self):
        return self._timestamp
