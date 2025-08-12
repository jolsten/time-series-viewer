import dash_bootstrap_components as dbc
from dash import dcc, html


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
