# lumat_app/acta_generator.py
# Genera el acta semestral del alumno en PDF usando reportlab.

import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ── Paleta ──────────────────────────────────────────────────
AZUL       = colors.HexColor("#4a7c7a")
AZUL_LIGHT = colors.HexColor("#e8f0ef")
GRIS_BORDE = colors.HexColor("#C8C0B4")
GRIS_BG    = colors.HexColor("#F7F4EF")
GRIS_TEXT  = colors.HexColor("#6B6560")
WARM       = colors.HexColor("#4a3f32")
BLANCO     = colors.white


def generar_acta_alumno(seminario, alumno, comite, datos_form):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    eyebrow = ParagraphStyle(
        "eyebrow", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica-Bold",
        textColor=AZUL, alignment=TA_CENTER,
        spaceAfter=2, letterSpacing=1.5,
    )
    titulo = ParagraphStyle(
        "titulo", parent=styles["Normal"],
        fontSize=18, fontName="Times-Bold",
        textColor=WARM, spaceAfter=2,
        alignment=TA_CENTER, leading=22,
    )
    subtitulo = ParagraphStyle(
        "subtitulo", parent=styles["Normal"],
        fontSize=10, fontName="Times-Roman",
        textColor=GRIS_TEXT, spaceAfter=0,
        alignment=TA_CENTER,
    )
    seccion = ParagraphStyle(
        "seccion", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=AZUL, spaceBefore=10, spaceAfter=3,
    )
    normal = ParagraphStyle(
        "normal_lumat", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        leading=13, textColor=WARM,
    )
    rol_style = ParagraphStyle(
        "rol", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica",
        textColor=GRIS_TEXT, alignment=TA_CENTER,
    )
    firma_nombre_style = ParagraphStyle(
        "firma_nombre", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=WARM, alignment=TA_CENTER, leading=11,
    )
    pie = ParagraphStyle(
        "pie", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica",
        textColor=GRIS_BORDE, alignment=TA_CENTER,
    )

    story = []
    d = datos_form

    # ── Encabezado en tabla (evita el empalme) ───────────────
    if seminario.fecha:
        semestre_label = (
            seminario.fecha.strftime("%Y")
            + f"-{seminario.fecha.month // 7 + 1}"
        )
        fecha_str = seminario.fecha.strftime("%d/%m/%Y")
    else:
        semestre_label = "Sin fecha"
        fecha_str = "Sin fecha asignada"

    # Encabezado compacto: todo en una sola celda separado por saltos de línea
    enc_text = (
        f"<font size='6' color='#4a7c7a'><b>SISTEMA DE GESTIÓN ACADÉMICA · LUMAT · UAZ</b></font><br/>"
        f"<font size='14' color='#4a3f32'><b>Informe Semestral del Alumno</b></font><br/>"
        f"<font size='8' color='#6B6560'>"
        f"Seminario {seminario.numero} &nbsp;·&nbsp; "
        f"Periodo {semestre_label} &nbsp;·&nbsp; Fecha: {fecha_str}"
        f"</font>"
    )
    enc_style = ParagraphStyle(
        "enc", parent=styles["Normal"],
        alignment=TA_CENTER, leading=16,
    )
    t_enc = Table([[Paragraph(enc_text, enc_style)]], colWidths=["100%"])
    t_enc.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), AZUL_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 1, AZUL),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(t_enc)
    story.append(Spacer(1, 6))

    # ── Datos del alumno ─────────────────────────────────────
    story.append(Paragraph("ALUMNO/A", seccion))
    nombre_completo = (
        f"{alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno}"
    )
    t_alumno = Table([
        [
            Paragraph(f"<b>Nombre:</b> {nombre_completo}", normal),
            Paragraph(f"<b>Matrícula:</b> {alumno.matricula or '—'}", normal),
        ],
        [
            Paragraph(f"<b>Correo:</b> {alumno.correo}", normal),
            Paragraph(f"<b>Semestre actual:</b> {alumno.semestre}°", normal),
        ],
        [
            Paragraph(f"<b>Posgrado:</b> {alumno.get_posgrado_display()}", normal),
            Paragraph(f"<b>Línea:</b> {alumno.get_linea_investigacion_display()}", normal),
        ],
    ], colWidths=["50%", "50%"])
    t_alumno.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND",    (0, 0), (-1, -1), GRIS_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t_alumno)

    # ── Comité ───────────────────────────────────────────────
    story.append(Paragraph("COMITÉ TUTOR", seccion))

    def nd(doc_obj):
        return f"{doc_obj.nombre} {doc_obj.apellido_paterno} {doc_obj.apellido_materno}"

    t_comite = Table([
        [
            Paragraph(f"<b>{nd(comite.tutor)}</b> <font color='#6B6560'>( Tutor )</font>", normal),
            Paragraph(f"Reuniones con tutor: <b>{d.get('reuniones_tutor', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.director)}</b> <font color='#6B6560'>( Director )</font>", normal),
            Paragraph(f"Reuniones con comité: <b>{d.get('reuniones_comite', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.coodirector)}</b> <font color='#6B6560'>( Coodirector )</font>", normal),
            Paragraph(f"Asistencias al Coloquio: <b>{d.get('coloquios', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.asesor)}</b> <font color='#6B6560'>( Asesor )</font>", normal),
            Paragraph("", normal),
        ],
    ], colWidths=["58%", "42%"])
    t_comite.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND",    (0, 0), (-1, -1), GRIS_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t_comite)

    # ── Secciones de actividades ─────────────────────────────
    story.append(Paragraph("ACTIVIDAD PRINCIPAL DURANTE EL SEMESTRE", seccion))
    story.append(_caja(d.get("actividad_principal", "—"), normal))

    story.append(Paragraph("CURSOS INSCRITOS", seccion))
    story.append(_caja(d.get("cursos") or "No inscribí ningún curso.", normal))

    story.append(Paragraph("ARTÍCULOS ENVIADOS / PUBLICADOS", seccion))
    story.append(_caja(d.get("articulos") or "No tengo artículos enviados o publicados.", normal))

    story.append(Paragraph("EVENTOS ACADÉMICOS / ESTANCIAS DE INVESTIGACIÓN", seccion))
    story.append(_caja(d.get("eventos") or "No asistí a ningún evento ni realicé alguna estancia.", normal))

    story.append(Paragraph("PLAN DE ACTIVIDADES PARA EL SIGUIENTE SEMESTRE", seccion))
    story.append(_caja(d.get("plan_siguiente", "—"), normal))

    coment = d.get("comentarios", "").strip()
    if coment:
        story.append(Paragraph("COMENTARIOS ADICIONALES", seccion))
        story.append(_caja(coment, normal))

    # ── Firmas ───────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=8))
    story.append(Paragraph("VISTO BUENO DEL COMITÉ TUTOR", seccion))
    story.append(Spacer(1, 6))

    def _celda_firma(docente_obj, rol_label):
        celda = []
        # Imagen de firma si existe
        if docente_obj.firma:
            try:
                ruta = docente_obj.firma.path
                if os.path.exists(ruta):
                    img = Image(ruta, width=2.5 * cm, height=1.0 * cm)
                    img.hAlign = "CENTER"
                    celda.append(img)
                else:
                    celda.append(Spacer(1, 1.0 * cm))
            except Exception:
                celda.append(Spacer(1, 1.0 * cm))
        else:
            celda.append(Spacer(1, 1.0 * cm))

        celda.append(Paragraph("_______________", firma_nombre_style))
        celda.append(Spacer(1, 3))
        celda.append(Paragraph(
            f"{docente_obj.nombre} {docente_obj.apellido_paterno}",
            firma_nombre_style,
        ))
        celda.append(Paragraph(rol_label, rol_style))
        return celda

    miembros_firma = [
        (comite.tutor,       "Tutor"),
        (comite.director,    "Director"),
        (comite.coodirector, "Coodirector"),
        (comite.asesor,      "Asesor"),
    ]

    t_firmas = Table(
        [[_celda_firma(doc_obj, rol_lbl) for doc_obj, rol_lbl in miembros_firma]],
        colWidths=["25%", "25%", "25%", "25%"],
    )
    t_firmas.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_firmas)

    # ── Pie ──────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=4))
    story.append(Paragraph(
        "Sistema de Gestión Académica LUMAT &nbsp;·&nbsp; Informe generado automáticamente",
        pie,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _caja(texto, style):
    t = Table(
        [[Paragraph(str(texto) if texto else "—", style)]],
        colWidths=["100%"],
    )
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND",    (0, 0), (-1, -1), GRIS_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return t