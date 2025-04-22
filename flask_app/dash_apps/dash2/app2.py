import pandas as pd
from dash import Dash, Input, Output, dash_table, html
from dash.dash_table.Format import Format, Group, Symbol
from flask import g


def init_app(url_path, server=None):
    global df
    global engine
    engine = g.engine

    app = Dash(__name__, server=server, routes_pathname_prefix=url_path)

    PAGE_SIZE = 10

    app.layout = [
        html.Nav(
            [
                html.A("Logout", href="/logout"),
                html.A("Menu", href="/dash"),
                html.A("Profile", href="/profile")
            ]
        ),
        html.H2("GapMinder 2025"),
        html.Hr(),
        dash_table.DataTable(
            id="table-sorting-filtering",
            columns=[
                {"name": "Country", "id": "country", "type": "text"},
                {
                    "name": "Population",
                    "id": "population",
                    "type": "numeric",
                    "format": Format(group=Group.yes, groups=3, group_delimiter=" "),
                },
                {
                    "name": "Life Expectation (Yrs)",
                    "id": "life_exp",
                    "type": "numeric",
                    "format": {"specifier": ",.1f"},
                },
                {
                    "name": "GDP per capita",
                    "id": "gdp_percap",
                    "type": "numeric",
                    "format": Format(symbol=Symbol.yes, symbol_prefix="$"),
                },
            ],
            style_cell_conditional=[
                {"if": {"column_type": "text"}, "textAlign": "left"}
            ],
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(220, 220, 220)",
                },
                {
                    "if": {
                        "column_id": "gdp_percap",
                        "filter_query": "{gdp_percap} > 50000",
                    },
                    "backgroundColor": "tomato",
                    "color": "white",
                },
            ],
            style_as_list_view=True,
            page_current=0,
            page_size=PAGE_SIZE,
            page_action="custom",
            filter_action="custom",
            filter_query="",
            sort_action="custom",
            sort_mode="single",
            sort_by=[],
        ),
    ]

    init_callbacks(app)
    return app.server


operators = [
    [">=", "ge ", ">="],
    ["<=", "le ", "<="],
    ["<", "lt ", "<"],
    [">", "gt ", ">"],
    ["<>", "ne ", "!="],
    ["=", "eq ", "="],
    ["like", "contains "],
]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find("{") + 1 : name_part.rfind("}")]

                value_part = value_part.strip()
                v0 = value_part[0]
                if v0 == value_part[-1] and v0 in ("'", '"', "`"):
                    value = value_part[1:-1].replace("\\" + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                return name, operator_type[0], value

    return [None] * 3


def update_table(page_current, page_size, sort_by, filter):
    filtering_expressions = filter.split(" && ")
    query_filter_parts = []
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)
        if col_name is None:
            continue
        if operator in ("=", "<>", "<", "<=", ">", ">="):
            query_filter_parts.append(
                col_name + " " + operator + " " + str(filter_value)
            )
        elif operator == "like":
            query_filter_parts.append(col_name + " like '%%" + filter_value + "%%'")

    query_filter = " and ".join(query_filter_parts)
    if len(query_filter):
        query_filter = " where " + query_filter

    sorting = ""
    if len(sort_by):
        sorting_parts = [col["column_id"] + " " + col["direction"] for col in sort_by]
        sorting = " order by " + ", ".join(sorting_parts)

    query = (
        "select country, population, life_exp, gdp_percap from gapminder"
        + query_filter
        + sorting
        + " offset "
        + str(page_current * page_size)
        + " limit "
        + str(page_size)
    )

    with engine.connect() as conn, conn.begin():
        df = pd.read_sql_query(query, conn)

    return df.to_dict("records")


def init_callbacks(app):
    app.callback(
        Output("table-sorting-filtering", "data"),
        Input("table-sorting-filtering", "page_current"),
        Input("table-sorting-filtering", "page_size"),
        Input("table-sorting-filtering", "sort_by"),
        Input("table-sorting-filtering", "filter_query"),
    )(update_table)
