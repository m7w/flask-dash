import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, ctx, dash_table, dcc, html
from flask import request


def init_app(url_path, server=None):
    global df

    df = px.data.tips()

    app = Dash(
        __name__,
        server=server,
        routes_pathname_prefix=url_path,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    app.layout = [
        html.Nav(
            [
                html.A("Logout", href="/logout"),
                html.A("Menu", href="/dash"),
                html.A("Profile", href="/profile"),
            ]
        ),
        dcc.Markdown(
            id="title-markdown", children="# Tips", style={"textAlign": "center"}
        ),
        dbc.Row(
            [
                dbc.Col(
                    dash_table.DataTable(
                        id="tips-table",
                        data=df.to_dict("records"),
                        columns=[
                            {"name": i, "id": i, "selectable": True} for i in df.columns
                        ],
                        column_selectable="single",
                        selected_columns=["tip"],
                        page_size=15,
                        editable=False,
                    ),
                    width=5,
                ),
                dbc.Col(dcc.Graph(id="total-bill-bar"), width=7),
            ]
        ),
        dbc.Col(
            dbc.Row([html.Div(id="table-triggered-message")]),
            width=5,
            style={"textAlign": "center"},
        ),
    ]

    init_callbacks(app)
    return app.server


def update_graph_message(data, selected_column, active_cell):
    triggered_prop_ids = ctx.triggered_prop_ids

    dff = pd.DataFrame(data)

    message = "Nothing selected yet"
    if "tips-table.selected_columns" in triggered_prop_ids:
        message = f"The selected columns is '{selected_column[0]}'"
    elif "tips-table.active_cell" in triggered_prop_ids:
        message = f"The data of the selected cell is '{
            dff.iloc[active_cell['row'], active_cell['column']]
        }'"

    figure = px.bar(dff, x="time", y="total_bill", color="day")
    return figure, message


def update_selected_style(columns):
    return [
        {"if": {"column_id": i}, "backgroundColor": "lightsteelblue"} for i in columns
    ]


def update_table_editable(_):
    permissions = request.cookies.get("permissions", "").split(",")
    return "user-write" in permissions


def init_callbacks(app):
    app.callback(
        Output("total-bill-bar", "figure"),
        Output("table-triggered-message", "children"),
        Input("tips-table", "data"),
        Input("tips-table", "selected_columns"),
        Input("tips-table", "active_cell"),
    )(update_graph_message)

    app.callback(
        Output("tips-table", "style_data_conditional"),
        Input("tips-table", "selected_columns"),
    )(update_selected_style)

    app.callback(Output("tips-table", "editable"), Input("tips-table", "start_cell"))(
        update_table_editable
    )
