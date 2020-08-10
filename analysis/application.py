"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""

import argparse
import os
import sys
import time

import psutil
import multiprocessing as mp
import queue
import subprocess

import redis

from .processor import DataProcessor, DataSimulator
from .zmq_streamer import DataClient, DataStreamer


def start_redis_server(host='127.0.0.1', port=6379, *, password=None):
    command = [
        "/home/xfeluser/extra-analysis/thirdparty/bin/redis-server",
        "--port", str(port)
    ]

    process = subprocess.Popen(command)

    client = redis.Redis(host=host, port=port)
    for i in range(5):
        try:
            var = client.ping()
            print(f"Attempt {i+1} to connect to redis succeeded:", var)
        except Exception as ex:
            time.sleep(2)
        else:
            break

    if process.poll() is None:
        print("Redis process is running...")
    else:
        print("Redis was terminated ...")


class Application:
    def __init__(self, hostname='127.0.0.1', port=6379, password=None):
        # start_redis_server()

        # raw container (mp.Queue) where data from DataSimulator is fed
        raw_queue = mp.Queue(maxsize=1)
        # processed container (mp.Queue) where data from DataProcessor is fed
        self.proc_queue = mp.Queue(maxsize=1)

        self.data_simulator = DataSimulator(raw_queue)
        self.data_processor = DataProcessor(raw_queue, self.proc_queue)

        # ZMQ dispatcher to send processed data over network
        self._zmq_dispatcher_buffer = queue.Queue(maxsize=10)
        self.data_streamer = DataStreamer(
            "tcp://*:54055", self._zmq_dispatcher_buffer)

    def start_app(self):
        # Start data simulator in a process
        self.data_simulator.start()
        # Start data processor in a process
        self.data_processor.start()
        # Start ZMQ dispatcher in Thread of parent process
        self.data_streamer.start()

        while True:
            try:
                # Get processed data from proc_queue mp.Queue
                processed_data = self.proc_queue.get_nowait()
                print("Integrated image received at :", processed_data.timestamp)
                # Feed processed data to zmq buffer queue.Queue
                self._zmq_dispatcher_buffer.put_nowait(processed_data)
            except (queue.Empty, queue.Full):
                continue


def start_pipeline():
    parser = argparse.ArgumentParser(prog="extra analysis")
    parser.add_argument("hostname", type=str, help="hostname")
    parser.add_argument('port', type=int, help="port")

    args = parser.parse_args()
    host = args.hostname
    if host not in ['localhost', '127.0.0.1']:
        print("Cannot connect to remote host")
        sys.exit(1)

    port = args.port

    app = Application(hostname=host, port=port)
    app.start_app()


def start_test_client():
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


if __name__ == "__main__":
    start_pipeline()
