from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLOR_SEQUENCE = [
    "#2563eb",
    "#059669",
    "#f59e0b",
    "#dc2626",
    "#7c3aed",
    "#0891b2",
    "#4b5563",
]


def empty_figure(title: str, message: str = "No data available") -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "#6b7280"},
            }
        ],
        height=360,
        template="plotly_white",
    )
    return figure


def line_chart(
    frame: pd.DataFrame,
    x: str,
    y: str | Sequence[str],
    title: str,
    color: str | None = None,
    markers: bool = True,
) -> go.Figure:
    if not _has_columns(frame, [x, *_as_list(y), *( [color] if color else [] )]):
        return empty_figure(title)
    return px.line(
        frame,
        x=x,
        y=y,
        color=color,
        markers=markers,
        title=title,
        template="plotly_white",
        color_discrete_sequence=COLOR_SEQUENCE,
    )


def bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str | Sequence[str],
    title: str,
    color: str | None = None,
    orientation: str = "v",
    barmode: str = "group",
) -> go.Figure:
    if not _has_columns(frame, [x, *_as_list(y), *( [color] if color else [] )]):
        return empty_figure(title)
    return px.bar(
        frame,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        barmode=barmode,
        title=title,
        template="plotly_white",
        color_discrete_sequence=COLOR_SEQUENCE,
    )


def scatter_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    size: str | None = None,
    hover_data: Sequence[str] | None = None,
) -> go.Figure:
    optional_columns = [column for column in [color, size, *(hover_data or [])] if column]
    if not _has_columns(frame, [x, y, *optional_columns]):
        return empty_figure(title)
    return px.scatter(
        frame,
        x=x,
        y=y,
        color=color,
        size=size,
        hover_data=list(hover_data or []),
        title=title,
        template="plotly_white",
        color_discrete_sequence=COLOR_SEQUENCE,
    )


def funnel_chart(frame: pd.DataFrame, stage_column: str, value_column: str, title: str) -> go.Figure:
    if not _has_columns(frame, [stage_column, value_column]):
        return empty_figure(title)
    figure = go.Figure(
        go.Funnel(
            y=frame[stage_column],
            x=frame[value_column],
            marker={"color": COLOR_SEQUENCE[: len(frame)]},
        )
    )
    figure.update_layout(title=title, template="plotly_white", height=420)
    return figure


def pie_chart(frame: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    if not _has_columns(frame, [names, values]):
        return empty_figure(title)
    return px.pie(
        frame,
        names=names,
        values=values,
        title=title,
        template="plotly_white",
        color_discrete_sequence=COLOR_SEQUENCE,
    )


def _has_columns(frame: pd.DataFrame, columns: Sequence[str]) -> bool:
    return not frame.empty and all(column in frame.columns for column in columns if column)


def _as_list(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value)
