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
from .redisdb import get_redis_client
from .webgui import DashApp
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
    def __init__(self, hostname, port, *,
                 redis_host='127.0.0.1', redis_port=6379, password=None):
        start_redis_server()

        # raw container (mp.Queue) where data from DataSimulator is fed
        raw_queue = mp.Queue(maxsize=1)
        # processed container (mp.Queue) where data from DataProcessor is fed
        self.proc_queue = mp.Queue(maxsize=1)

        self.data_simulator = DataSimulator(raw_queue)
        self.data_processor = DataProcessor(raw_queue, self.proc_queue)

        # ZMQ dispatcher to send processed data over network
        self._zmq_dispatcher_buffer = queue.Queue(maxsize=1)
        if hostname == "localhost":
            hostname = '*'
        self.data_streamer = DataStreamer(
            f"tcp://{hostname}:{port}", self._zmq_dispatcher_buffer)

    def start_app(self):
        # Start data simulator in a process
        self.data_simulator.start()
        # Start data processor in a process
        self.data_processor.start()
        # Start ZMQ dispatcher in Thread of parent process
        self.data_streamer.start()

        client = get_redis_client()

        while True:
            try:
                # Get processed data from proc_queue mp.Queue
                processed_data = self.proc_queue.get_nowait()
                print("Integrated image received at :", processed_data.timestamp)
                # Feed processed data to zmq buffer queue.Queue
                self._zmq_dispatcher_buffer.put_nowait(processed_data)
                client.set("TimeStamp", processed_data.timestamp)
            except (queue.Empty, queue.Full):
                continue


def start_pipeline():
    parser = argparse.ArgumentParser(prog="extra analysis")
    parser.add_argument("hostname", type=str, help="hostname")
    parser.add_argument("port", type=int,
                        help="ZMQ port to stream processed data")
    parser.add_argument("--redis_host", type=str,
                        help="redis-hostname")
    parser.add_argument('--redis_port', type=int,
                        help="redis-port", required=False)

    args = parser.parse_args()
    host = args.hostname
    port = args.port

    redis_host = args.redis_host
    redis_port = args.redis_port

    if redis_host and redis_host not in ['localhost', '127.0.0.1']:
        print("Cannot connect to remote host")
        sys.exit(1)

    app = Application(host, port)
    app.start_app()


def start_test_client():
    import matplotlib.pyplot as plt
    import numpy as np

    client = DataClient("tcp://127.0.0.1:54055")
    fig = plt.figure(figsize=(8, 8), constrained_layout=True)
    gs = fig.add_gridspec(2,2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    while True:
        msg = client.next()
        ax1.imshow(msg.mean_image, cmap='jet')
        ax1.set_title("Raw image")
        ax2.imshow(np.mean(msg.edges, axis=0), cmap='gray')
        ax2.set_title("Edge detection")
        for i in range(msg.intensities.shape[0]):
            ax3.plot(msg.momentum, msg.intensities[i], label=f"Pulse {i}")
            ax3.set_title(f'Integrated image')
        ax3.set_xlabel("q")
        ax3.set_ylabel("I(q)")
        ax3.legend(loc='upper left')
        fig.suptitle(f'Processed image : {msg.timestamp}')
        plt.pause(0.01)
        plt.cla()


def start_dash_client():

    # app = DashApp('127.0.0.1', 54055)
    app = DashApp()

    app._app.run_server(debug=False)

if __name__ == "__main__":
    start_pipeline()
