from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1
from reportlab.lib.units import mm

from .get_product_name import get_product_name
from .models import CatalogProduct, StockEntry, TripPlan
from .money_value import money_value

from fsstock.ui.colors.colors import BG_DARK, BG_DARK_2, PRIMARY_GREEN


# =================================================================================================
# Helpers
# =================================================================================================

def _exports_dir(user_data_dir: str) -> Path:
    """
    Returns the directory where to export the report.
    
    Parameters
    ----------
    user_data_dir: str
        Directory where to save files
    
    Returns
    -------
    d: Path
        he directory where to export the report:
        user_data_dir/exports
    """
    d = Path(user_data_dir) / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _fmt_int(x: float) -> str:
    """
    Converts the float into a string format:
    1234567.89 -> "1 234 568"
    
    Parameters
    ----------
    x: float
        The number to convert
        
    """
    return f"{x:,.0f}".replace(",", " ")

# =================================================================================================
# Main PDF export
# =================================================================================================
 
def export_pdf_report(
    user_data_dir: str,
    catalog: dict[str, CatalogProduct],
    stock: list[StockEntry],
    last_plan: TripPlan | None = None,
    *,
    filename: str | None = None,
    title: str = "FS Stock Report",
    farm_name: str = "",
) -> Path:
    """
    Generates a PDF with:
    - Current stock table
    - Totals
    - (Optional) Target plan if last_plan exists and is feasible
    
    Parameters
    ----------
    user_data_dir: str
        Directory where to save files
    catalog: dict[str, CatalogProduct]
        Catalog of all items
    stock: list[StockEntry]
        List of all the items in stock
    last_plan: TripPlan | None (optional)
        Trip plan, if exists
    filename: str | None (optional)
        Name of the output PDF
    title: str (default = "FS Stock Report")
        Title of the PDF
    farm_name: str (default = "")
        Farm name
    
    Returns
    -------
    Path
        The path to the created PDF.
    """
    out_dir: Path = _exports_dir(user_data_dir)  # Output directory

    # Default filename 
    if filename is None:
        stamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename: str = f"fs_stock_report_{stamp}.pdf"

    out_path: Path = out_dir / filename  # Output path

    styles: StyleSheet1 = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "h1",
        parent=styles["Heading1"],
        fontSize=20,
        alignment=TA_LEFT,
        spaceAfter=6,
        textColor=PRIMARY_GREEN
    )
    h2 = ParagraphStyle(
        "h2",
        parent=styles["Heading2"],
        fontSize=14,
        alignment=TA_LEFT,
        spaceAfter=4,
        textColor=PRIMARY_GREEN
    )
    meta = ParagraphStyle(
        "meta",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_LEFT,
    )
    normal = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontSize=12,
        alignment=TA_LEFT,
    )

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=title,
    )

    story: list[Any] = []

    # -------- Header --------
    # Title
    if farm_name:
        story.append(Paragraph(f"{title} - {farm_name}", h1))
    else:
        story.append(Paragraph(title, h1))
    
    # Subtitle
    dt_str: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Generado: {dt_str}", meta))
    if farm_name:
        story.append(Paragraph(f"Granja: <b>{farm_name}</b>", meta))
    story.append(Spacer(1, 10))

    # -------- Stock table --------
    story.append(Paragraph("Stock actual", h2))

    # Header table
    data: list[list[str]] = [[
        "Producto",
        "Cantidad\n(L)",
        "Precio máx\n(€/1000L)",
        "Valor\n(€)",
        "Cap/viaje\n(L)",
        "Mínimo\n(L)",
        "Vendible",
    ]]

    total_value: float = 0.0

    # Orden por valor descendente
    sorted_stock: list[StockEntry] = sorted(
        stock,
        key=lambda e: money_value(e.qty_l, e.max_price_per_1000),
        reverse=True,
    )

    for e in sorted_stock:
        val: float = money_value(e.qty_l, e.max_price_per_1000)
        total_value += val

        data.append([
            get_product_name(e.product_id, catalog),
            _fmt_int(e.qty_l),
            _fmt_int(e.max_price_per_1000),
            _fmt_int(val),
            _fmt_int(e.cap_per_trip_l),
            _fmt_int(e.min_keep_l),
            "Sí" if e.enabled_for_optimization else "No",
        ])

    # Totals
    story.append(Paragraph(f"<b>Valor total:</b> {_fmt_int(total_value)} €", normal))
    story.append(Spacer(1, 6))

    # Table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_GREEN)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor(BG_DARK), colors.HexColor(BG_DARK_2)]),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    table.hAlign = "LEFT"
    story.append(table)
    story.append(Spacer(1, 14))

    # -------- Objective plan section (optional) --------
    if last_plan:
        story.append(Paragraph("Plan de objetivo", h2))
        story.append(Paragraph(
            f"<b>Objetivo:</b> {_fmt_int(last_plan.target_eur)} € &nbsp;&nbsp; "
            f"<b>Viajes:</b> {last_plan.total_trips} &nbsp;&nbsp; "
            f"<b>Ingreso estimado:</b> {_fmt_int(last_plan.total_revenue_eur)} €",
            normal,
        ))
        story.append(Spacer(1, 6))

        data2: list[list[str]] = [[
            "Producto",
            "Viajes",
            "Cap/viaje\n(L)",
            "Viaje extra\n(L)",
            "Vender\n(L)",
            "Ingreso\n(€)",
            "Stock restante\n(L)",
        ]]

        # Current stock
        stock_map: dict[str, StockEntry] = {e.product_id: e for e in stock}

        for ln in last_plan.lines:
            name: str = get_product_name(ln.product_id, catalog)

            e: StockEntry = stock_map[ln.product_id]
            current_qty: float = e.qty_l if e else 0.0
            cap: float = (e.cap_per_trip_l if e else 0.0) or 0.0

            # Amount of extra trip (if exists)
            if ln.last_partial_used and cap > 0:
                extra_l: float = max(0.0, ln.sold_l - ln.full_trips * cap)
            elif ln.last_partial_used:
                # If there is no defined cap,
                # we assume that everything sold is "extra"
                extra_l: float = ln.sold_l
            else:
                extra_l: float = 0.0

            trips_str: str = (
                str(ln.full_trips) \
                if not ln.last_partial_used \
                else f"{ln.full_trips}+1" if ln.full_trips > 0 else "1"
            )
            remaining: float = max(current_qty - ln.sold_l, 0.0)

            data2.append([
                name,
                trips_str,
                _fmt_int(cap),
                _fmt_int(extra_l),
                _fmt_int(ln.sold_l),
                _fmt_int(ln.revenue_eur),
                _fmt_int(remaining),
            ])

        table2 = Table(data2, repeatRows=1)
        table2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#88b00e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#262626"), colors.HexColor("#525252")]),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 1), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        table2.hAlign = "LEFT"
        story.append(table2)
        story.append(Spacer(1, 8))

    doc.build(story)
    return out_path
