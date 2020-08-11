"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
All rights reserved.
"""
from math import ceil
import numpy as np
import queue
from queue import Queue

import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from .layout import get_layout
from ..config import config

import psutil as ps

def get_virtual_memory():
    virtual_memory, swap_memory = ps.virtual_memory(), ps.swap_memory()
    return virtual_memory, swap_memory


class DashApp:

    def __init__(self, hostname, port):
        app = dash.Dash(__name__)
        app.config['suppress_callback_exceptions'] = True
        self._hostname = hostname
        self._port = port
        self._app = app
        self._config = config

        self.setLayout()
        self.register_callbacks()

    def setLayout(self):
        self._app.layout = get_layout(config["TIME_OUT"], self._config)

    def register_callbacks(self):
        """Register callbacks"""
        pass
