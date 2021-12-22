"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""
import argparse
import multiprocessing as mp
import os
import queue
import sys
import time
from getpass import getuser

import redis
from compose.cli.main import TopLevelCommand, project_from_options

from analysis.config import command_docker_options
from analysis.processor.data_processor import DataProcessor
from analysis.processor.data_simulator import DataSimulator
from analysis.redisdb import get_redis_client
from analysis.webgui.app import DashApp
from analysis.zmq_streamer.data_streamer import DataClient, DataStreamer


def run_redis_container(cmd, options):
    print("Starting redis container ...", flush=True)
    cmd.up(options)


def build_and_run():
    options = command_docker_options
    options["--project-name"] = "analysis-pipeline"
    options["--file"] = ["compose/docker-compose-redis.yml"]
    project = project_from_options(os.path.dirname(os.path.dirname(__file__)), options)
    cmd = TopLevelCommand(project)
    run_redis_container(cmd, options)
    return cmd, options


def start_redis_server():
    cmd, options = build_and_run()

    client = redis.Redis(host="127.0.0.1", port=6379)
    is_redis_up = False
    for i in range(5):
        try:
            client.ping()
            is_redis_up = True
            print(f"Attempt {i+1} to connect to redis succeeded:")
        except Exception:
            time.sleep(2)
        else:
            break

    return is_redis_up, cmd, options


class Application:
    def __init__(self, hostname, port):
        is_redis_up, self.docker_command, self.docker_options = start_redis_server()

        if not is_redis_up:
            self.docker_command.down(self.docker_options)
            sys.exit(1)

        # raw container (mp.Queue) where data from DataSimulator is fed
        raw_queue = mp.Queue(maxsize=1)
        # processed container (mp.Queue) where data from DataProcessor is fed
        self.proc_queue = mp.Queue(maxsize=1)

        self.data_simulator = DataSimulator(raw_queue)
        self.data_processor = DataProcessor(raw_queue, self.proc_queue)

        # ZMQ dispatcher to send processed data over network
        self._zmq_dispatcher_buffer = queue.Queue(maxsize=1)
        if hostname == "localhost":
            hostname = "*"
        self.data_streamer = DataStreamer(
            f"tcp://{hostname}:{port}", self._zmq_dispatcher_buffer
        )

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

    def stop_app(self):
        self.docker_command.down(self.docker_options)
        self.data_streamer.stop()
        if self.data_streamer and self.data_streamer.is_alive():
            self.data_streamer.join()
        if self.data_simulator and self.data_simulator.is_alive():
            self.data_simulator.join()
        if self.data_processor and self.data_processor.is_alive():
            self.data_processor.join()


def start_pipeline():
    parser = argparse.ArgumentParser(prog="extra analysis")
    parser.add_argument("hostname", type=str, help="hostname")
    parser.add_argument("port", type=int, help="ZMQ port to stream processed data")
    parser.add_argument("--redis_host", type=str, help="redis-hostname")
    parser.add_argument("--redis_port", type=int, help="redis-port", required=False)

    args = parser.parse_args()
    host = args.hostname
    port = args.port

    app = Application(host, port)
    try:
        app.start_app()
    except KeyboardInterrupt:
        print(f"Interrupted by user: {getuser()}. Closing consumers ...")
    finally:
        app.stop_app()


def start_test_client():
    import matplotlib.pyplot as plt
    import numpy as np

    client = DataClient("tcp://127.0.0.1:54055")
    fig = plt.figure(figsize=(8, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    while True:
        msg = client.next()
        ax1.imshow(msg.mean_image, cmap="jet")
        ax1.set_title("Raw image")
        ax2.imshow(np.mean(msg.edges, axis=0), cmap="gray")
        ax2.set_title("Edge detection")
        for i in range(msg.intensities.shape[0]):
            ax3.plot(msg.momentum, msg.intensities[i], label=f"Pulse {i}")
            ax3.set_title("Integrated image")
        ax3.set_xlabel("q")
        ax3.set_ylabel("I(q)")
        ax3.legend(loc="upper left")
        fig.suptitle(f"Processed image : {msg.timestamp}")
        plt.pause(0.01)
        plt.cla()


def start_dash_client():

    # app = DashApp('127.0.0.1', 54055)
    app = DashApp()

    app._app.run_server(debug=False)


if __name__ == "__main__":
    # start_pipeline()
    start_redis_server()
