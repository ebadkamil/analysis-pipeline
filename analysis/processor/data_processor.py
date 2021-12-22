"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""

import multiprocessing as mp
import queue

import numpy as np

from analysis.processor.azimuthal_integration import ImageIntegrator
from analysis.processor.canny_edge import EdgeDetection
from analysis.redisdb import DashMeta, get_redis_client, str2tuple


class DataProcessor(mp.Process):
    def __init__(self, data_in, data_out):
        super().__init__()

        self._data_in = data_in
        self._data_out = data_out
        self._running = False

        self.integrator = ImageIntegrator()
        self.edge_detector = EdgeDetection()
        self._db = get_redis_client()
        self._dmt = DashMeta()

    def run(self):
        self._running = True

        while self._running:
            try:
                raw = self._data_in.get_nowait()
            except queue.Empty:
                continue

            mean_image, momentum, intensities, edges = self.process(raw)

            proc_data = IntegratedData(raw[0]["timestamp"])
            proc_data.mean_image = mean_image
            proc_data.momentum = momentum
            proc_data.intensities = intensities
            proc_data.edges = edges

            while self._running:
                try:
                    self._data_out.put_nowait(proc_data)
                    break
                except queue.Full:
                    continue

    def process(self, raw):
        try:
            cfg = self._db.hgetall(self._dmt.AZIMUTHAL_META)
        except Exception as ex:
            print("[REDIS] ", ex)

        if not cfg:
            cfg = dict(
                energy="9.3",
                pixel_size="0.5e-3",
                centrex="128",
                centrey="128",
                distance="0.2",
                intg_rng="[0., 2]",
                intg_method="BBox",
                intg_pts="512",
                threshold_mask="(0,12)",
                user_mask=None,
            )

        meta, data = raw
        config = dict(
            energy=float(cfg["energy"]),
            pixel_size=float(cfg["pixel_size"]),
            centrex=float(cfg["centrex"]),
            centrey=float(cfg["centrey"]),
            distance=float(cfg["distance"]),
            intg_rng=str2tuple(cfg["intg_rng"]),
            intg_method="BBox",
            intg_pts=int(cfg["intg_pts"]),
            threshold_mask=str2tuple(cfg["threshold_mask"]),
            user_mask=None,
        )

        image = data["image"]
        mom, intensities = self.integrator.integrate(config, image)
        edges = self.edge_detector.find_edges(image)
        return np.mean(image, axis=0), mom, intensities, edges


class IntegratedData:
    def __init__(self, timestamp):
        self._timestamp = timestamp
        self.mean_image = None
        self.momentum = None
        self.intensities = None
        self.edges = None

    @property
    def timestamp(self):
        return self._timestamp
