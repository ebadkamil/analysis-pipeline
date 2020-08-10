"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""

from datetime import datetime
import time
import multiprocessing as mp
import queue

from scipy import ndimage as ndi
import numpy as np


class DataSimulator(mp.Process):
    def __init__(self, sim_queue, data_shape=None):
        super().__init__()

        self._sim_queue = sim_queue
        self._data_shape = data_shape
        self._running = False

    def run(self):
        self._running = True

        while self._running:
            shape = self._data_shape \
                if self._data_shape is not None else (2, 1024, 1024)

            choices = ["circles", "squares"]
            choice = np.random.choice(choices)
            background =  2. * np.random.rand(*shape)
            if choice == "circles":
                # Random image data emulating rings
                x = np.linspace(-1, 1, shape[-2])
                y = np.linspace(-1, 1, shape[-1])
                xx, yy = np.meshgrid(x, y)
                z = 10. * np.sin(
                    np.random.randint(1, 20) * np.pi * (xx**2 + yy**2))
            else:
                z = np.zeros(shape[1:])
                x = np.random.randint(0, 512)
                z[x:-x, x:-x] = 10.

                z = ndi.rotate(
                    z, np.random.randint(10, 45),
                    mode='constant', reshape=False)

            data = {'image': background + z}
            meta = {'timestamp': datetime.now().strftime(
                    "%d-%b-%Y (%H:%M:%S.%f)")}

            payload = (meta, data)
            try:
                self._sim_queue.put_nowait(payload)
                time.sleep(.1)
            except queue.Full:
                continue

    def terminate(self):
        self._running = False


if __name__ == "__main__":
    sim_queue = mp.Queue(maxsize=1)
    simulator = DataSimulator(sim_queue)
    simulator.daemon = True
    simulator.start()
    while True:
        try:
            meta, data = sim_queue.get_nowait()
            print(meta)
        except queue.Empty:
            continue
    simulator.terminate()
