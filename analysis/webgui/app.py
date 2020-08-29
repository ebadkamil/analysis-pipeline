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
from ..redisdb import get_redis_client, DashMeta
from ..zmq_streamer import DataClient

import psutil as ps

def get_virtual_memory():
    virtual_memory, swap_memory = ps.virtual_memory(), ps.swap_memory()
    return virtual_memory, swap_memory


class DashApp:

    def __init__(self):
        app = dash.Dash(__name__)
        app.config['suppress_callback_exceptions'] = True
        self._app = app
        self._config = config
        self._data_client = None
        self._db = get_redis_client()
        self._dmt = DashMeta()

        self.setLayout()
        self.register_callbacks()

    def setLayout(self):
        self._app.layout = get_layout(config["TIME_OUT"], self._config)

    def register_callbacks(self):
        """Register callbacks"""
        @self._app.callback(
            Output('stream-info', 'children'),
            [Input('start', 'on')],
            [State('hostname', 'value'),
             State('port', 'value')])
        def stream(state, hostname, port):
            info = ""
            if state:
                if not (hostname and port):
                    info = f"Either hostname or port number missing"
                    return [info]
                print("Address ", f"tcp://{hostname}:{port}")
                self._data_client = DataClient(f"tcp://{hostname}:{port}")
                info = f"Listening to tcp://{hostname}:{port}"

            elif not state:
                self._data_client = None

            return [info]

        @self._app.callback(
            Output('timestamp', 'value'),
            [Input('interval_component', 'n_intervals')])
        def update_train_id(n):
            self._update()
            if self._data is None:
                raise dash.exceptions.PreventUpdate
            return str(self._data.timestamp)

        @self._app.callback(
            [Output('virtual_memory', 'value'),
             Output('virtual_memory', 'max'),
             Output('swap_memory', 'value'),
             Output('swap_memory', 'max')],
            [Input('psutil_component', 'n_intervals')])
        def update_memory_info(n):
            try:
                virtual, swap = get_virtual_memory()
            except Exception:
                raise dash.exceptions.PreventUpdate
            return ((virtual.used/1024**3), ceil((virtual.total/1024**3)),
                    (swap.used/1024**3), ceil((swap.total/1024**3)))

        @self._app.callback(Output('mean-image', 'figure'),
                            [Input('color-scale', 'value'),
                             Input('timestamp', 'value')])
        def update_image_figure(color_scale, timestamp):
            if self._data.timestamp != timestamp or self._data.mean_image is None:
                raise dash.exceptions.PreventUpdate

            traces = [go.Heatmap(
                z=self._data.mean_image, colorscale=color_scale)]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                    title="Raw Image",
                )
            }

            return figure

        @self._app.callback(Output('mean-edges', 'figure'),
                            [Input('color-scale', 'value'),
                             Input('timestamp', 'value')])
        def update_edge_figure(color_scale, timestamp):
            if self._data.timestamp != timestamp or self._data.edges is None:
                raise dash.exceptions.PreventUpdate

            traces = [go.Heatmap(
                z=np.mean(self._data.edges, axis=0),
                colorscale=color_scale)]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                    title="Edge detection",
                )
            }

            return figure

        @self._app.callback(Output('histogram', 'figure'),
                            [Input('timestamp', 'value')])
        def update_histogram_figure(timestamp):
            if self._data.timestamp != timestamp or self._data.mean_image is None:
                raise dash.exceptions.PreventUpdate
            hist, bins = np.histogram(self._data.mean_image.ravel(), bins=100)
            bin_center = (bins[1:] + bins[:-1])/2.0
            traces = [{'x': bin_center, 'y': hist,
                       'type': 'bar'}]
            figure = {
                'data': traces,
                'layout': go.Layout(
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                )
            }

            return figure

        @self._app.callback(Output('ai-integral', 'figure'),
                            [Input('timestamp', 'value')],
                            [State('n-pulses', 'value')]
                            )
        def update_correlation_figure(timestamp, pulses):
            if self._data.timestamp != timestamp or self._data is None:
                raise dash.exceptions.PreventUpdate

            try:
                y = getattr(self._data, "intensities")
                x = getattr(self._data, "momentum")
                traces = [go.Scatter(x=x, y=y[i], name=f"Pulse {i}")
                          for i in range(y[:pulses, ...].shape[0])]
            except Exception as ex:
                raise dash.exceptions.PreventUpdate

            figure = {
                'data': traces,
                'layout': go.Layout(
                    xaxis={'title': 'q'},
                    yaxis={'title': 'I(q)'},
                    margin={'l': 40, 'b': 40, 't': 40, 'r': 10},
                    hovermode='closest',
                    showlegend=True,
                    title="Integrated Image",)}

            return figure

        @self._app.callback(Output('logger', 'children'),
                            [Input('energy', 'value'),
                             Input('distance', 'value'),
                             Input('pixel-size', 'value'),
                             Input('centrex', 'value'),
                             Input('centrey', 'value'),
                             Input('int-mthd', 'value'),
                             Input('int-pts', 'value'),
                             Input('int-rng', 'value'),
                             Input('mask-rng', 'value')]
                            )
        def update_params(energy,
                          distance,
                          pixel_size,
                          centerx,
                          centery,
                          int_mthd,
                          int_pts,
                          int_rng,
                          mask_rng):

            ai_config  = dict(energy=energy,
                pixel_size=pixel_size,
                centrex=centerx,
                centrey=centery,
                distance=distance,
                intg_rng=str(int_rng),
                intg_method=int_mthd,
                intg_pts=int_pts,
                threshold_mask=str(mask_rng))

            try:
                self._db.hmset(self._dmt.AZIMUTHAL_META, ai_config)
            except Exception as ex:
                print("[REDIS] ", ex)
            return f"Redis Hash set: {ai_config}"

    def _update(self):
        self._data = None
        if self._data_client is not None:
            try:
                self._data = self._data_client.next()
            except Exception as ex:
                print(ex)
                pass
