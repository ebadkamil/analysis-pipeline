"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""
import pickle
import queue
from threading import Thread
import zmq


class DataStreamer(Thread):
    def __init__(self, endpoint, buffer, sock='REP'):
        super().__init__()
        self._context = zmq.Context()

        if sock != "REP":
            raise NotImplementedError(f"Socket type {sock} not implemented")

        self._socket = self._context.socket(zmq.REP)
        self._socket.bind(endpoint)

        self._buffer = buffer

    def run(self):
        try:
            while True:
                req = self._socket.recv()
                if req == b"next":
                    try:
                        msg = self._buffer.get()
                        self._socket.send(pickle.dumps(msg))
                        print("Dispatched data to zmq client ...")
                    except queue.Empty:
                        continue
        except Exception as ex:
            print("Exception ", ex)

        finally:
            self._socket.setsockopt(zmq.LINGER, 0)
            self._socket.close()


class DataClient:

    def __init__(self, endpoint, sock="REQ"):
        super().__init__()
        self._context = zmq.Context()
        if sock != "REQ":
            raise NotImplementedError(f"Socket type {sock} not implemented")

        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(endpoint)

    def next(self):
        req = self._socket.send(b"next")
        message = self._socket.recv()
        return pickle.loads(message)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    client = DataClient("tcp://127.0.0.1:54055")
    fig, ax = plt.subplots(1,2, figsize=(15, 7))
    while True:
        msg = client.next()
        ax[0].imshow(msg.mean_image[::2, ::2])
        for i in range(msg.intensities.shape[0]):
            ax[1].plot(msg.momentum, msg.intensities[i], label=f"Pulse {i}")
            ax[1].set_title(f'Integrated image : {msg.timestamp}')
        ax[1].legend()
        plt.tight_layout()
        plt.pause(0.01)
        plt.cla()
