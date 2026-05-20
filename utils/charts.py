"""
Utility chart functions for property investment analysis.
"""

import plotly.graph_objects as go


def create_radar_chart(
    property_scores: dict,
    barrio_avg: dict,
    property_name: str = "Esta propiedad",
    barrio_name: str = "Media del barrio",
    height: int = 400,
) -> go.Figure:
    """Radar (spider) chart comparando scores de una propiedad vs. media del barrio.

    Args:
        property_scores: Dict con keys score_* de la propiedad seleccionada.
        barrio_avg: Dict con keys score_* para el promedio del barrio.
        property_name: Label para la traza de la propiedad.
        barrio_name: Label para la traza del barrio.
        height: Alto del chart en píxeles.

    Returns:
        go.Figure de Plotly.
    """
    score_keys = [
        "score_descuento",
        "score_precio",
        "score_liquidez",
        "score_tamano",
        "score_ruido",
    ]

    labels = [
        "Descuento",
        "Precio vs Barrio",
        "Liquidez",
        "Tamaño",
        "Ruido",
    ]

    prop_vals = [float(property_scores.get(k, 0) or 0) for k in score_keys]
    barrio_vals = [float(barrio_avg.get(k, 0) or 0) for k in score_keys]

    all_vals = prop_vals + barrio_vals
    max_val = max(all_vals) if all_vals else 30

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=prop_vals + [prop_vals[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name=property_name,
        line=dict(color="#2E86AB", width=2),
        fillcolor="rgba(46, 134, 171, 0.15)",
    ))

    fig.add_trace(go.Scatterpolar(
        r=barrio_vals + [barrio_vals[0]],
        theta=labels + [labels[0]],
        fill="none",
        name=barrio_name,
        line=dict(color="#A23B72", width=2, dash="dot"),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max_val * 1.15, 30)],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#555"),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
        height=height,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#333"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )

    return fig


def create_price_history_chart(
    history: pd.DataFrame,
    height: int = 120,
    show_xaxis: bool = False,
    color: str = "#2E86AB",
) -> go.Figure:
    """Mini sparkline del historico de precios."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=history["fecha"],
        y=history["precio"],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba(46, 134, 171, 0.1)",
        name="Precio",
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f}€<extra></extra>",
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(
            visible=show_xaxis,
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            visible=False,
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
    )
    return fig


def _hex_to_rgba(hex_color: str, alpha: float = 0.12) -> str:
    """Convierte color hex a string rgba."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


COLORS_PALETTE = ["#2E86AB", "#A23B72", "#F18F01", "#3B8C5C", "#C73E3E"]


def create_comparison_radar(
    properties: list[dict],
    property_names: list[str] | None = None,
    height: int = 450,
) -> go.Figure:
    """Radar chart con múltiples propiedades superpuestas para comparación visual.

    Args:
        properties: Lista de dicts con keys score_*.
        property_names: Nombres para cada propiedad (misma longitud que properties).
        height: Alto del chart.

    Returns:
        go.Figure de Plotly.
    """
    score_keys = [
        "score_descuento", "score_precio", "score_liquidez",
        "score_tamano", "score_ruido",
    ]
    labels = [
        "Descuento", "Precio vs Barrio", "Liquidez",
        "Tamaño", "Ruido",
    ]

    fig = go.Figure()

    for i, prop in enumerate(properties):
        vals = [float(prop.get(k, 0) or 0) for k in score_keys]
        name = property_names[i] if property_names else f"#{i + 1}"
        color = COLORS_PALETTE[i % len(COLORS_PALETTE)]

        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=labels + [labels[0]],
            fill="toself",
            name=name,
            line=dict(color=color, width=2),
            fillcolor=_hex_to_rgba(color, 0.12),
        ))

    all_vals = [v for p in properties for k in score_keys for v in [float(p.get(k, 0) or 0)]]
    max_val = max(all_vals) if all_vals else 30

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max_val * 1.15, 30)],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(tickfont=dict(size=11, color="#555")),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
        height=height,
        margin=dict(l=60, r=60, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#333"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )

    return fig
