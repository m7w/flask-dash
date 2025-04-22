import locale

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html


def init_app(url_path, server=None):
    global df

    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

    global labelalias
    labelalias = {
        "Jan": "Янв",
        "Feb": "Фев",
        "Mar": "Мар",
        "Apr": "Апр",
        "May": "Mай",
        "Jun": "Июн",
        "Jul": "Июл",
        "Aug": "Авг",
        "Sep": "Сен",
        "Oct": "Окт",
        "Nov": "Ноя",
        "Dec": "Дек",
    }

    df = pd.read_excel("data/dashboard.xlsx")
    df.set_index("Дата", inplace=True)

    months = df.index.to_period("M").unique()
    month_nums = range(0, len(months) + 1)
    strings = months.strftime("%b-%Y")
    global dates
    dates = months.strftime("%Y-%m-%d")
    first_date = df.index.min() - pd.DateOffset(days=1)  # pyright: ignore [reportOperatorIssue]
    dates = dates.insert(0, first_date.strftime("%Y-%m-%d"))
    slicer_marks = dict(zip(month_nums, strings))

    customers = df["Заказчик"].unique()
    cities = df["Город"].unique()

    # external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    # app = Dash(__name__, external_stylesheets=external_stylesheets)
    app = Dash(
        __name__,
        server=server,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        routes_pathname_prefix=url_path,
    )

    app.layout = [
        html.Nav(
            [
                html.A("Logout", href="/logout"),
                html.A("Menu", href="/dash"),
                html.A("Profile", href="/profile")
            ]
        ),
        html.H2("Отчет о продажах"),
        html.Hr(),
        dcc.Graph(figure=create_trend_graph()),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Checklist(
                            [
                                {"label": html.Span(i, className="button"), "value": i}
                                for i in customers
                            ],
                            value=customers,
                            labelClassName="custom-checkbox",
                            style={"margin": 30},
                            id="customer-checklist",
                        ),
                        dcc.Checklist(
                            [
                                {"label": html.Span(i, className="button"), "value": i}
                                for i in cities
                            ],
                            value=cities,
                            labelClassName="custom-checkbox",
                            style={"margin": 30},
                            id="city-checklist",
                        ),
                    ],
                    width=2,
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(id="category-bar"), width=6),
                                dbc.Col(dcc.Graph(id="product-bar"), width=6),
                            ],
                            style={"marginBottom": 40},
                        ),
                        dcc.RangeSlider(
                            min=month_nums[0],
                            max=month_nums[-1],
                            value=[month_nums[0], month_nums[-1]],
                            step=1,
                            marks=slicer_marks,
                            included=True,
                            updatemode="mouseup",
                            id="date-range-slider",
                        ),
                    ],
                ),
            ],
        ),
    ]

    init_callbacks(app)
    return app.server


def create_trend_graph():
    trend_data = df.resample("1ME")["Итого"].sum().div(10**6).round(decimals=2)
    figure = px.area(
        trend_data,
        y="Итого",
        range_y=[trend_data.min() - 10, trend_data.max() + 5],
        range_x=[
            trend_data.index.min() - pd.DateOffset(days=10),
            trend_data.index.max() + pd.DateOffset(days=10),
        ],
        text="Итого",
    )
    figure.update_traces(textposition="top center")
    figure.update_layout(
        margin=dict(l=10, t=50, r=10, b=10),
        xaxis=dict(title=None, tick0=trend_data.index[0]),
        yaxis=dict(title=None, showticklabels=False),
        title={
            "text": "Динамика продаж, млн рублей",
            "x": 0.5,
            "y": 0.9,
            "xanchor": "center",
            "yanchor": "bottom",
        },
    )
    figure.update_xaxes(dtick="M1", tickformat="%b", labelalias=labelalias)
    return figure


def create_category_product_bar(customers, cities, date_range):
    if customers is None or cities is None:
        return {}

    start_date = pd.Timestamp(dates[date_range[0]]) + pd.DateOffset(days=1)
    end_date = pd.Timestamp(dates[date_range[1]])

    ddf = df[start_date:end_date]
    cc_ddf = ddf[ddf["Заказчик"].isin(customers) & ddf["Город"].isin(cities)]

    category_data = cc_ddf.groupby("Категория товара")["Итого"].sum()

    c_figure = px.bar(
        category_data,
        y="Итого",
        text_auto=".4s",
    )
    c_figure.update_traces(textposition="outside")
    c_figure.update_layout(
        yaxis=dict(title=None, range=[0, max(category_data) * 1.15]),
        xaxis_title=None,
        margin=dict(l=10, t=50, r=10, b=10),
        title={
            "text": "Категории товаров, млн рублей",
            "x": 0.5,
            "y": 0.9,
            "xanchor": "center",
            "yanchor": "bottom",
        },
    )

    product_data = cc_ddf.groupby("Товар")["Итого"].sum().sort_values()  # pyright: ignore [reportCallIssue]

    p_figure = px.bar(
        product_data,
        x="Итого",
        text_auto=".4s",
        orientation="h",
    )
    p_figure.update_traces(textposition="outside")
    p_figure.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode="show",
        yaxis=dict(title=None, showticklabels=True, nticks=len(product_data)),
        xaxis=dict(title=None, range=[0, max(product_data) * 1.15]),
        margin=dict(l=10, t=50, r=10, b=10),
        title={
            "text": "Продажи товаров",
            "x": 0.5,
            "y": 0.9,
            "xanchor": "center",
            "yanchor": "bottom",
        },
    )
    return c_figure, p_figure


def update_output(value):
    return 'You have selected "{} - {}"'.format(dates[value[0]], dates[value[1]])


def init_callbacks(app):
    app.callback(
        Output("output-slider", "children"), Input("date-range-slider", "value")
    )(update_output)

    app.callback(
        Output("category-bar", "figure"),
        Output("product-bar", "figure"),
        Input("customer-checklist", "value"),
        Input("city-checklist", "value"),
        Input("date-range-slider", "value"),
    )(create_category_product_bar)
