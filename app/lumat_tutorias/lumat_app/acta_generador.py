# lumat_app/acta_generator.py
# Genera el acta semestral del alumno en PDF usando reportlab.

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ── Paleta ──────────────────────────────────────────────────
AZUL      = colors.HexColor("#2C5F8A")
GRIS_BORDE = colors.HexColor("#C8C0B4")
GRIS_BG   = colors.HexColor("#F7F4EF")
NEGRO     = colors.black
BLANCO    = colors.white


def generar_acta_alumno(seminario, alumno, comite, datos_form):
    """
    Genera el acta semestral del alumno como BytesIO con contenido PDF.

    Parámetros
    ----------
    seminario   : objeto Seminario
    alumno      : objeto Alumno
    comite      : objeto Comite
    datos_form  : dict con los campos del formulario llenado por el alumno:
        - actividad_principal  str
        - cursos               str
        - articulos            str
        - eventos              str
        - plan_siguiente       str
        - comentarios          str
        - reuniones_tutor      int
        - reuniones_comite     int
        - coloquios            int
    """
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

    # ── Estilos personalizados ───────────────────────────────
    titulo = ParagraphStyle(
        "titulo",
        parent=styles["Normal"],
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=AZUL,
        spaceAfter=2,
        alignment=1,  # centrado
    )
    subtitulo = ParagraphStyle(
        "subtitulo",
        parent=styles["Normal"],
        fontSize=13,
        fontName="Helvetica",
        textColor=AZUL,
        spaceAfter=4,
        alignment=1,
    )
    seccion = ParagraphStyle(
        "seccion",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=AZUL,
        spaceBefore=10,
        spaceAfter=3,
    )
    normal = ParagraphStyle(
        "normal_lumat",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        leading=13,
    )
    pie = ParagraphStyle(
        "pie",
        parent=styles["Normal"],
        fontSize=7,
        fontName="Helvetica",
        textColor=colors.HexColor("#6B6560"),
        alignment=1,
    )

    story = []

    # ── Encabezado ───────────────────────────────────────────
    story.append(Paragraph("INFORME SEMESTRAL", titulo))
    semestre_label = seminario.fecha.strftime("%Y") + f"-{seminario.fecha.month // 7 + 1}"
    story.append(Paragraph(f"Seminario {seminario.numero} &nbsp;·&nbsp; Semestre {semestre_label}", subtitulo))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL, spaceAfter=8))

    # ── Datos del alumno ────────────────────────────────────
    story.append(Paragraph("Alumno/a:", seccion))

    nombre_completo = f"{alumno.nombre} {alumno.apellido_paterno} {alumno.apellido_materno}"
    datos_alumno = [
        [
            Paragraph(f"<b>Nombre:</b> {nombre_completo}", normal),
            Paragraph(f"<b>Matrícula:</b> {alumno.matricula or '—'}", normal),
        ],
        [
            Paragraph(f"<b>Email:</b> {alumno.correo}", normal),
            Paragraph(f"<b>Semestre actual:</b> {alumno.semestre}°", normal),
        ],
    ]
    t_alumno = Table(datos_alumno, colWidths=["50%", "50%"])
    t_alumno.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t_alumno)

    # ── Comité tutor ────────────────────────────────────────
    story.append(Paragraph("Comité Tutor:", seccion))

    d = datos_form
    miembros = [
        [
            Paragraph(
                f"Dr./Dra. {comite.tutor.nombre} {comite.tutor.apellido_paterno} "
                f"<font color='#6B6560'>( Tutor Principal )</font>",
                normal,
            ),
            Paragraph(
                f"Me reuní <b>{d.get('reuniones_tutor', 0)}</b> veces con mi <b>tutor principal</b>.",
                normal,
            ),
        ],
        [
            Paragraph(
                f"Dr./Dra. {comite.miembro1.nombre} {comite.miembro1.apellido_paterno} "
                f"<font color='#6B6560'>( Miembro Tutor 1 )</font>",
                normal,
            ),
            Paragraph(
                f"Me reuní <b>{d.get('reuniones_comite', 0)}</b> veces con mi <b>comité tutor</b>.",
                normal,
            ),
        ],
        [
            Paragraph(
                f"Dr./Dra. {comite.miembro2.nombre} {comite.miembro2.apellido_paterno} "
                f"<font color='#6B6560'>( Miembro Tutor 2 )</font>",
                normal,
            ),
            Paragraph(
                f"Asistí <b>{d.get('coloquios', 0)}</b> veces al <b>Coloquio</b>.",
                normal,
            ),
        ],
    ]
    t_comite = Table(miembros, colWidths=["55%", "45%"])
    t_comite.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t_comite)

    # ── Actividad principal ──────────────────────────────────
    story.append(Paragraph("Actividad principal durante el semestre:", seccion))
    story.append(_caja(d.get("actividad_principal", "—"), normal))

    # ── Cursos ───────────────────────────────────────────────
    story.append(Paragraph("Cursos:", seccion))
    story.append(_caja(d.get("cursos", "No inscribí ningún curso."), normal))

    # ── Artículos ────────────────────────────────────────────
    story.append(Paragraph("Artículos enviados/publicados:", seccion))
    story.append(_caja(d.get("articulos", "No tengo artículos enviados o publicados."), normal))

    # ── Eventos ─────────────────────────────────────────────
    story.append(Paragraph("Asistencia a Eventos Académicos / Estancias:", seccion))
    story.append(_caja(d.get("eventos", "No asistí a ningún evento ni realicé alguna estancia."), normal))

    # ── Plan siguiente semestre ──────────────────────────────
    story.append(Paragraph("Plan de Actividades para el siguiente semestre:", seccion))
    story.append(_caja(d.get("plan_siguiente", "—"), normal))

    # ── Comentarios ─────────────────────────────────────────
    story.append(Paragraph("Comentarios Adicionales:", seccion))
    story.append(_caja(d.get("comentarios", ""), normal))

    # ── Espacio para firmas ──────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=10))
    story.append(Paragraph("<b>Visto Bueno</b>", ParagraphStyle(
        "vb", parent=normal, alignment=1, spaceBefore=4, spaceAfter=12,
    )))

    firmas = [
        [
            Paragraph(f"Dr./Dra. {comite.tutor.nombre} {comite.tutor.apellido_paterno}", normal),
            Paragraph(f"Dr./Dra. {comite.miembro1.nombre} {comite.miembro1.apellido_paterno}", normal),
            Paragraph(f"Dr./Dra. {comite.miembro2.nombre} {comite.miembro2.apellido_paterno}", normal),
        ],
        [
            Paragraph("_______________________", normal),
            Paragraph("_______________________", normal),
            Paragraph("_______________________", normal),
        ],
        [
            Paragraph("Tutor Principal", ParagraphStyle("rol", parent=normal, textColor=colors.HexColor("#6B6560"))),
            Paragraph("Miembro Tutor 1", ParagraphStyle("rol", parent=normal, textColor=colors.HexColor("#6B6560"))),
            Paragraph("Miembro Tutor 2", ParagraphStyle("rol", parent=normal, textColor=colors.HexColor("#6B6560"))),
        ],
    ]
    t_firmas = Table(firmas, colWidths=["33%", "34%", "33%"])
    t_firmas.setStyle(TableStyle([
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_firmas)

    # ── Pie de página ────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS_BORDE, spaceAfter=4))
    story.append(Paragraph(
        "Sistema de Gestión Académica LUMAT &nbsp;·&nbsp; Informe generado automáticamente",
        pie,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Helper ───────────────────────────────────────────────────

def _caja(texto, style):
    """Envuelve un texto en una tabla de una celda con borde y fondo."""
    t = Table(
        [[Paragraph(texto or "—", style)]],
        colWidths=["100%"],
    )
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#C8C0B4")),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F7F4EF")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return t