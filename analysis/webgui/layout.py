"""
Image analysis and web visualization

Author: Ebad Kamil <kamilebad@gmail.com>
All rights reserved.
"""
import dash_daq as daq
from dash import dcc, html

colors_map = ["jet", "Reds", "Viridis", "gray"]


def get_stream_tab(config):
    return html.Div(
        className="control-tab",
        children=[
            html.Br(),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Hostname"),
                            dcc.Input(
                                id="hostname",
                                placeholder="Enter the hostname",
                                type="text",
                                value=config["hostname"],
                            ),
                            html.Label("Port"),
                            dcc.Input(
                                id="port",
                                placeholder="Port",
                                type="text",
                                value=config["port"],
                            ),
                            html.Hr(),
                            daq.BooleanSwitch(id="start", on=False),
                        ],
                        className="pretty_container one-third column",
                    ),
                    html.Div(id="stream-info", className="two-thirds column"),
                ],
                className="row",
            ),
        ],
    )


def get_plot_tab(config):
    div = html.Div(
        children=[
            html.Br(),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Azimuthal Integration Set up"),
                            html.Hr(),
                            html.Label("Energy:", className="leftbox"),
                            dcc.Input(
                                id="energy",
                                type="number",
                                value=config["energy"],
                                className="rightbox",
                            ),
                            html.Label("Sample Distance:", className="leftbox"),
                            dcc.Input(
                                id="distance",
                                type="number",
                                value=config["distance"],
                                className="rightbox",
                            ),
                            html.Label("Pixel size:", className="leftbox"),
                            dcc.Input(
                                id="pixel-size",
                                type="number",
                                value=config["pixel_size"],
                                className="rightbox",
                            ),
                            html.Label("Cx (pixel):", className="leftbox"),
                            dcc.Input(
                                id="centrex",
                                type="number",
                                value=config["centerx"],
                                className="rightbox",
                            ),
                            html.Label("Cy (pixel)::", className="leftbox"),
                            dcc.Input(
                                id="centrey",
                                type="number",
                                value=config["centery"],
                                className="rightbox",
                            ),
                            html.Label("Integration Method:", className="leftbox"),
                            dcc.Dropdown(
                                id="int-mthd",
                                options=[
                                    {"label": i, "value": i}
                                    for i in config["int_mthds"]
                                ],
                                value=config["int_mthds"][0],
                                className="rightbox",
                            ),
                            html.Label("Integration points:", className="leftbox"),
                            dcc.Input(
                                id="int-pts",
                                type="number",
                                value=config["int_pts"],
                                className="rightbox",
                            ),
                        ],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            html.Label("Edge detection set up"),
                            html.Hr(),
                            html.Label("Sigma:", className="leftbox"),
                            dcc.Dropdown(
                                id="sigma",
                                options=[
                                    {"label": i, "value": i} for i in range(1, 4, 1)
                                ],
                                value=3,
                            ),
                            html.Hr(),
                            html.Label("Apply Gaussian filter:", className="leftbox"),
                            dcc.Checklist(
                                options=[
                                    {"value": "apply_filter"},
                                ],
                                value=["apply_filter"],
                                className="rightbox",
                            ),
                            html.Label("Integration range:", className="leftbox"),
                            dcc.RangeSlider(
                                id="int-rng",
                                min=0,
                                max=10.0,
                                value=config["int_rng"],
                                className="rightbox",
                            ),
                            html.Label("Mask range:", className="leftbox"),
                            dcc.RangeSlider(
                                id="mask-rng",
                                min=0,
                                max=10000.0,
                                value=config["mask_rng"],
                                className="rightbox",
                            ),
                            html.Div(id="logger"),
                        ],
                        className="pretty_container six columns",
                    ),
                ],
                className="row",
            ),
            html.Hr(),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="color-scale",
                                options=[{"label": i, "value": i} for i in colors_map],
                                value=colors_map[0],
                            )
                        ],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [
                            html.Label("Pulses: ", className="leftbox"),
                            dcc.Slider(
                                id="n-pulses",
                                min=1,
                                max=400,
                                value=10,
                                step=1,
                                className="rightbox",
                            ),
                        ],
                        className="pretty_container six columns",
                    ),
                ],
                className="row",
            ),
            html.Hr(),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="mean-image")],
                        className="pretty_container six columns",
                    ),
                    html.Div(
                        [dcc.Graph(id="mean-edges")],
                        className="pretty_container six columns",
                    ),
                ],
                className="row",
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="histogram")],
                        className="pretty_container four columns",
                    ),
                    html.Div(
                        [dcc.Graph(id="ai-integral")],
                        className="pretty_container eight columns",
                    ),
                ],
                className="row",
            ),
        ]
    )
    return div


def get_layout(UPDATE_INT, config=None):

    app_layout = html.Div(
        [
            html.Div(
                [
                    dcc.Interval(
                        id="interval_component",
                        interval=UPDATE_INT * 1000,
                        n_intervals=0,
                    ),
                    dcc.Interval(
                        id="psutil_component", interval=2 * 1000, n_intervals=0
                    ),
                ],
                style=dict(textAlign="center"),
            ),
            html.Div(
                [
                    daq.Gauge(
                        id="virtual_memory",
                        min=0,
                        value=0,
                        size=150,
                        className="leftbox",
                        style=dict(textAlign="center"),
                    ),
                    daq.Gauge(
                        id="swap_memory",
                        min=0,
                        value=0,
                        size=150,
                        className="rightbox",
                        style=dict(textAlign="center"),
                    ),
                ]
            ),
            daq.LEDDisplay(
                id="timestamp",
                value="1000",
                color="#FF5E5E",
                style=dict(textAlign="center"),
            ),
            html.Br(),
            html.Div(
                children=[
                    dcc.Tabs(
                        parent_className="custom-tabs",
                        className="custom-tabs-container",
                        id="view-tabs",
                        value="plot",
                        children=[
                            dcc.Tab(
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                                label="Stream/Load data",
                                value="stream-data",
                                children=get_stream_tab(config),
                            ),
                            dcc.Tab(
                                className="custom-tab",
                                selected_className="custom-tab--selected",
                                label="Plots",
                                value="plot",
                                children=get_plot_tab(config),
                            ),
                        ],
                    )
                ]
            ),
        ]
    )

    return app_layout
