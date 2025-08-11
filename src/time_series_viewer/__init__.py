import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.subplots as ps
import polars as pl
from dash import Dash, Input, Output, State, callback, dcc, html
from plotly_resampler import FigureResampler, register_plotly_resampler

register_plotly_resampler(mode="auto", default_n_shown_samples=10_000)


def make_select_modal(choices):
    body = []
    for i in range(4):
        body.append(
            html.Div(
                [
                    html.Label(f"Subplot {i + 1}"),
                    dcc.Dropdown(
                        choices,
                        [],
                        id=f"select-dropdown-{i}",
                        multi=True,
                    ),
                ],
                className="mb-3",
            )
        )

    modal = dbc.Modal(
        children=[
            dbc.ModalHeader(dbc.ModalTitle("Selection"), close_button=True),
            dbc.ModalBody(body),
            dbc.ModalFooter(
                [
                    # dbc.Button("Apply", id="select-modal-apply"),
                    dbc.Button("Close", id="select-modal-cancel"),
                ]
            ),
        ],
        id="select-modal-dismiss",
        backdrop="static",
        # fullscreen=True,
        size="xl",
        is_open=False,
    )
    return modal


def create_graph(df: pl.DataFrame):
    graph = dcc.Graph(id="graph", responsive=True)

    @callback(
        Output("graph", "figure"),
        [Input(f"select-dropdown-{i}", "value") for i in range(4)],
    )
    def update_graph_selection(*subplots):
        # Only keep subplots with selections (not empty)
        subplots = [subplot for subplot in subplots if subplot]
        plot_count = len(subplots)

        if plot_count == 0:
            return go.Figure()

        fig = ps.make_subplots(
            rows=plot_count, cols=1, shared_xaxes=True, vertical_spacing=0.02
        )
        fig.update_layout(margin={"l": 1, "r": 1, "t": 1, "b": 1})
        fig = FigureResampler(fig)

        for row, subplot in enumerate(subplots, start=1):
            for col in subplot:
                x = df["time"]
                y = df[col]
                trace = go.Scattergl(mode="markers", name=col, showlegend=True)
                fig.add_trace(trace, row=row, col=1, hf_x=x, hf_y=y)
        return fig

    return html.Div(graph, style={"height": "85vh"})


def main() -> None:
    df = pl.read_parquet("data/big.parquet").with_row_index()
    df = df.to_pandas()

    app = Dash(name=__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    graph = create_graph(df)

    nav = dbc.Navbar(
        [
            dbc.NavItem(dbc.NavbarBrand("App Name")),
            dbc.NavItem(
                dbc.Button(
                    "Select",
                    id="select-modal-open",
                    active=True,
                )
            ),
        ],
        color="primary",
        dark=True,
    )
    data_cols = [*df.columns]
    data_cols.remove("time")
    select_modal = make_select_modal(data_cols)

    @callback(
        Output("select-modal-dismiss", "is_open"),
        [
            Input("select-modal-open", "n_clicks"),
            # Input("select-modal-apply", "n_clicks"),
            Input("select-modal-cancel", "n_clicks"),
        ],
        [State("select-modal-dismiss", "is_open")],
    )
    def toggle_modal(n_open, n_cancel, is_open):
        if n_open:
            return not is_open
        return is_open

    app.layout = [
        html.H1(children="App Title", style={"textAlign": "center"}),
        nav,
        select_modal,
        html.Div(
            children=[graph],
            className="container-fluid",
            style={"width": "100%", "height": "100%"},
        ),
    ]

    app.run(debug=True)
