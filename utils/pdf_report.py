import io
from datetime import datetime
from fpdf import FPDF


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Vivienda AI - Madrid Investment Intelligence", align="L")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | Pagina {self.page_no()}/{{nb}}", align="C")


def generar_informe_propiedad(prop: dict) -> bytes:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Título ──
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "Informe de Propiedad", new_x="LMARGIN", new_y="NEXT")

    barrio = prop.get("barrio", "Sin barrio")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Barrio: {barrio}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Decisión ──
    decision = str(prop.get("decision", ""))
    if "COMPRAR" in decision:
        dec_label, dec_color = "COMPRAR", (34, 197, 94)
    elif "NEGOCIAR" in decision:
        dec_label, dec_color = "NEGOCIAR", (245, 158, 11)
    else:
        dec_label, dec_color = "DESCARTAR", (239, 68, 68)

    pdf.set_fill_color(*dec_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"  Decision: {dec_label}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── KPIs ──
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Indicadores principales", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    rows = [
        ("Precio total", f"{int(prop.get('precio_total', 0)):,} EUR"),
        ("Superficie", f"{int(prop.get('metros', 0))} m2"),
        ("Precio por m2", f"{int(prop.get('precio_m2', 0)):,} EUR/m2"),
        ("Score total", f"{round(prop.get('score_total', 0), 1)} / 100"),
        ("Rentabilidad estimada", f"{round(prop.get('rentabilidad_estimada', 0), 1)} %"),
    ]
    if prop.get("rooms"):
        rows.append(("Habitaciones", str(int(prop["rooms"]))))
    if prop.get("bathrooms"):
        rows.append(("Banos", str(int(prop["bathrooms"]))))

    pdf.set_font("Helvetica", "", 10)
    for label, val in rows:
        pdf.set_text_color(60, 60, 60)
        pdf.cell(80, 7, label, border=0)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, val, border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Desglose de scoring ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Desglose del scoring", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    score_rows = [
        ("Descuento", prop.get("score_descuento", 0)),
        ("Precio vs Barrio", prop.get("score_precio", 0)),
        ("Liquidez", prop.get("score_liquidez", 0)),
        ("Tamano", prop.get("score_tamano", 0)),
        ("Ruido", prop.get("score_ruido", 0)),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, val in score_rows:
        pdf.set_text_color(60, 60, 60)
        pdf.cell(80, 7, label, border=0)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, f"{round(val, 1) if val else 0}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ── Simulacion financiera ──
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Simulacion financiera", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    precio = prop.get("precio_total", 0)
    metros = prop.get("metros", 0)
    entrada_pct = 0.2
    interes = 0.035
    anos = 25
    entrada = precio * entrada_pct
    gastos = precio * 0.10
    prestamo = precio - entrada
    r = interes / 12
    n = anos * 12
    cuota = round(prestamo * (r * (1 + r)**n) / ((1 + r)**n - 1), 2) if prestamo else 0
    alquiler_est = round(metros * 20 * 1.15, 2)
    cashflow = round(alquiler_est - cuota - alquiler_est * 0.15 - 100, 2)

    fin_rows = [
        ("Entrada (20%)", f"{int(entrada):,} EUR"),
        ("Gastos compra (10%)", f"{int(gastos):,} EUR"),
        ("Prestamo", f"{int(prestamo):,} EUR"),
        ("Cuota mensual", f"{cuota:,.2f} EUR"),
        ("Alquiler estimado", f"{alquiler_est:,.2f} EUR"),
        ("Cashflow mensual", f"{cashflow:,.2f} EUR"),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, val in fin_rows:
        pdf.set_text_color(60, 60, 60)
        pdf.cell(80, 7, label, border=0)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, val, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Disclaimer ──
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, (
        "Este informe se genera con datos historicos (Idealista18, 2018) y estimaciones automaticas. "
        "No constituye asesoramiento financiero. Verifique toda la informacion antes de tomar decisiones de inversion."
    ))

    return pdf.output()


def generar_informe_top3(top3: list[dict]) -> bytes:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "Top 3 - Oportunidades de Inversion", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for i, prop in enumerate(top3, 1):
        if i > 1:
            pdf.add_page()

        decision = str(prop.get("decision", ""))
        if "COMPRAR" in decision:
            dec_label, dec_color = "COMPRAR", (34, 197, 94)
        elif "NEGOCIAR" in decision:
            dec_label, dec_color = "NEGOCIAR", (245, 158, 11)
        else:
            dec_label, dec_color = "DESCARTAR", (239, 68, 68)

        pdf.set_fill_color(*dec_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"  #{i}  {prop.get('barrio', 'Sin barrio')} - {dec_label}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 10)
        data = [
            ("Precio", f"{int(prop.get('precio_total', 0)):,} EUR"),
            ("Score", f"{round(prop.get('score_total', 0), 1)} / 100"),
            ("Rentabilidad", f"{round(prop.get('rentabilidad_estimada', 0), 1)} %"),
            ("Superficie", f"{int(prop.get('metros', 0))} m2"),
        ]
        if prop.get("rooms"):
            data.append(("Habitaciones", str(int(prop["rooms"]))))
        for label, val in data:
            pdf.set_text_color(60, 60, 60)
            pdf.cell(60, 7, label, border=0)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 7, val, new_x="LMARGIN", new_y="NEXT")

    pdf.set_text_color(150, 150, 150)
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 4, "Datos historicos Idealista18 (2018). No constituye asesoramiento financiero.")

    return pdf.output()
