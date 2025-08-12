""""""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.subplots as ps
import polars as pl
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash_extensions.enrich import DashProxy, Serverside, ServersideOutputTransform
from plotly_resampler import FigureResampler

# --------------------------------------Globals ---------------------------------------

SELECT_MODAL = "select-modal"
SELECT_MODAL_BODY = "select-modal-body"
SELECT_MODAL_OPEN = "select-modal-open"
SELECT_MODAL_CANX = "select-modal-cancel"
SELECT_MODAL_APPLY = "select-modal-apply"
SELECT_FILE = "select-file"
GRAPH = "graph"

MAX_SUBPLOTS = 4
FIGURE_MARGIN = {"l": 1, "r": 1, "t": 30, "b": 1}

app = DashProxy(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    transforms=[ServersideOutputTransform()],
)
nav = dbc.Navbar(
    [
        dbc.NavItem(
            dbc.Button(
                "Select",
                id=SELECT_MODAL_OPEN,
                active=True,
            )
        ),
    ],
    color="primary",
    dark=True,
)

modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Selection"), close_button=True),
        dbc.ModalBody(
            [
                dcc.Dropdown(["data/big.parquet"], id=SELECT_FILE),
                *[
                    html.Div(
                        [
                            html.Label(f"Subplot {i + 1}"),
                            dcc.Dropdown([], [], id=f"select-dropdown-{i}", multi=True),
                        ],
                        className="mb-3",
                    )
                    for i in range(MAX_SUBPLOTS)
                ],
            ],
            id=SELECT_MODAL_BODY,
        ),
        dbc.ModalFooter(
            [
                dbc.Button("Apply", id=SELECT_MODAL_APPLY, n_clicks=0),
                dbc.Button("Close", id=SELECT_MODAL_CANX),
            ]
        ),
    ],
    id=SELECT_MODAL,
    backdrop="static",
    size="xl",
    is_open=False,
)

app.layout = html.Div(
    [
        nav,
        modal,
        # The graph object - which we will empower with plotly-resampler
        dcc.Graph(id=GRAPH, responsive=True, style={"height": "85vh"}),
        # Note: we also add a dcc.Store component, which will be used to link the
        #       server side cached FigureResampler object
        dcc.Loading(dcc.Store(id="store")),
    ]
)


# ------------------------------------ DASH logic -------------------------------------
# The callback used to construct and store the FigureResampler on the serverside
@app.callback(
    output=[Output(GRAPH, "figure"), Output("store", "data")],
    inputs=dict(
        n_clicks=Input(SELECT_MODAL_APPLY, "n_clicks"),
        file=State(SELECT_FILE, "value"),
        subplots=[State(f"select-dropdown-{i}", "value") for i in range(MAX_SUBPLOTS)],
    ),
    prevent_initial_call=True,
)
def plot_graph(n_clicks, file, subplots):
    ctx = callback_context
    if not (len(ctx.triggered) and SELECT_MODAL_APPLY in ctx.triggered[0]["prop_id"]):
        # If the "Apply" button was not the trigger, provide no update
        return no_update

    fig: FigureResampler = FigureResampler(
        go.Figure()  # , default_downsampler=MinMaxLTTB(parallel=True)
    )
    fig.update_layout(margin=FIGURE_MARGIN)

    subplots = [subplot for subplot in subplots if subplot]
    plot_count = len(subplots)

    if plot_count == 0:
        fig = fig.replace(go.Figure())
        fig.update_layout(margin=FIGURE_MARGIN)
        return fig, Serverside(fig)

    # Figure construction logic
    fig.replace(
        ps.make_subplots(
            rows=plot_count, cols=1, shared_xaxes=True, vertical_spacing=0.02
        )
    )
    fig.update_layout(margin=FIGURE_MARGIN)

    df = pl.scan_parquet(file)
    x = df.select("time").collect().to_numpy().transpose()[0]
    for row, subplot in enumerate(subplots, start=1):
        for col in subplot:
            y = df.select(col).collect().to_numpy().transpose()[0]
            trace = go.Scattergl(mode="markers", name=col, showlegend=True)
            fig.add_trace(trace, row=row, col=1, hf_x=x, hf_y=y, max_n_samples=10_000)

    return fig, Serverside(fig)


# The plotly-resampler callback to update the graph after a relayout event (= zoom/pan)
# As we use the figure again as output, we need to set: allow_duplicate=True
@app.callback(
    Output(GRAPH, "figure", allow_duplicate=True),
    Input(GRAPH, "relayoutData"),
    State("store", "data"),  # The server side cached FigureResampler per session
    prevent_initial_call=True,
    memoize=True,
)
def update_fig(relayoutdata: dict, fig: FigureResampler):
    if fig is None:
        return no_update
    return fig.construct_update_data_patch(relayoutdata)


@app.callback(
    Output(SELECT_MODAL, "is_open"),
    [
        Input(SELECT_MODAL_OPEN, "n_clicks"),
        Input(SELECT_MODAL_CANX, "n_clicks"),
    ],
    [State(SELECT_MODAL, "is_open")],
)
def toggle_modal(n_open, n_cancel, is_open):
    if n_open:
        return not is_open
    return is_open


@app.callback(
    [
        *[Output(f"select-dropdown-{i}", "options") for i in range(MAX_SUBPLOTS)],
    ],
    Input(SELECT_FILE, "value"),
)
def select_data_file(file):
    if file is None:
        return [], [], [], []
    columns = pl.scan_parquet(file).collect_schema().names()
    return columns, columns, columns, columns


def main():
    app.run(debug=True)
