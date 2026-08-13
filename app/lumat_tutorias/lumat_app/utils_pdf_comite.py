# utils_pdf_comite.py — coloca este archivo en lumat_app/utils_pdf_comite.py
"""Genera el PDF del Informe Semestral del Comité Tutor sobre una plantilla membretada.

Forzado a 1 sola página con paleta institucional UAZ / LUMAT.
"""

import io
import os
from django.conf import settings
from pypdf import PdfReader, PdfWriter

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image,
)
from reportlab.lib.enums import TA_CENTER


# ── Paleta Institucional (UAZ / LUMAT) ────────────────────────
NAVY_PRIMARY = colors.HexColor("#1A2B4C")  # Azul marino institucional
GOLD_ACCENT  = colors.HexColor("#B38E46")  # Dorado/Bronce decorativo
BG_SOFT      = colors.HexColor("#F8FAFC")  # Fondo limpio ligeramente gris
BORDER_SOFT  = colors.HexColor("#CBD5E1")  # Borde suave neutro
TEXT_MAIN    = colors.HexColor("#1E293B")  # Texto oscuro de alto contraste
TEXT_MUTED   = colors.HexColor("#64748B")  # Texto secundario/desactivado


def _styles():
    s = {}

    s['titulo'] = ParagraphStyle(
        'titulo', fontName='Helvetica-Bold',
        fontSize=12, leading=14, alignment=TA_CENTER, textColor=NAVY_PRIMARY)

    s['subtitulo'] = ParagraphStyle(
        'subtitulo', fontName='Helvetica',
        fontSize=8, leading=10, alignment=TA_CENTER, textColor=TEXT_MUTED)

    s['label'] = ParagraphStyle(
        'label', fontName='Helvetica-Bold',
        fontSize=7.5, leading=10, textColor=NAVY_PRIMARY)

    s['value'] = ParagraphStyle(
        'value', fontName='Helvetica',
        fontSize=8, leading=11, textColor=TEXT_MAIN)

    s['section'] = ParagraphStyle(
        'section', fontName='Helvetica-Bold',
        fontSize=8, leading=10, textColor=NAVY_PRIMARY,
        spaceBefore=4, spaceAfter=2)

    s['body'] = ParagraphStyle(
        'body', fontName='Helvetica',
        fontSize=8, leading=11, textColor=TEXT_MAIN)

    s['firma_nombre'] = ParagraphStyle(
        'firma_nombre', fontName='Helvetica-Bold',
        fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=NAVY_PRIMARY)

    s['firma_rol'] = ParagraphStyle(
        'firma_rol', fontName='Helvetica-Bold',
        fontSize=6.5, leading=8, alignment=TA_CENTER, textColor=TEXT_MUTED)

    return s


def _hr():
    return HRFlowable(width='100%', thickness=0.6,
                      color=GOLD_ACCENT, spaceAfter=4, spaceBefore=2)


def _box_table(content_rows, style_extra=None):
    """Crea una tabla estilizada con bordes suaves e interiores limpios."""
    base_style = [
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ('BACKGROUND', (0, 0), (-1, -1), BG_SOFT),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]
    if style_extra:
        base_style += style_extra
    t = Table(content_rows, colWidths=['100%'])
    t.setStyle(TableStyle(base_style))
    return t


def generar_pdf_comite(formulario) -> bytes:
    """Recibe una instancia de FormularioComite con .seminario pre-cargado.

    Devuelve los bytes del PDF montado sobre la plantilla membretada (fuerza 1 sola hoja).
    """
    buf = io.BytesIO()
    
    # Margen superior e inferior optimizados para no tocar el membrete
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=3.6 * cm, bottomMargin=2.2 * cm,
    )
    S = _styles()
    sem = formulario.seminario
    al = sem.alumno
    com = sem.comite
    story = []

    # ── Encabezado Tipográfico Limpio (Sin Cuadro) ───────────
    story.append(Paragraph('INFORME SEMESTRAL DEL COMITÉ TUTOR', S['titulo']))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f'Semestre: {sem.numero}', S['subtitulo']))
    story.append(_hr())

    # ── Datos del alumno ──────────────────────────────────────
    story.append(Paragraph('ALUMNO/A', S['section']))

    alumno_data = [
        [Paragraph(
            f'<b>Nombre:</b> {al.nombre} {al.apellido_paterno} {al.apellido_materno}', S['value'])],
        [Paragraph(
            f'<b>Matrícula:</b> {al.matricula or "—"} &nbsp;&nbsp;&nbsp;&nbsp; '
            f'<b>Semestre:</b> {al.semestre}° &nbsp;&nbsp;&nbsp;&nbsp; '
            f'<b>Correo:</b> {al.correo}', S['value'])],
    ]
    story.append(_box_table(alumno_data))

    # ── Comité ────────────────────────────────────────────────
    story.append(Paragraph('COMITÉ TUTOR', S['section']))

    def docente_str(d):
        if not d:
            return "—"
        return f'{d.nombre} {d.apellido_paterno} {d.apellido_materno}'

    fecha_str = sem.fecha.strftime("%d/%m/%Y") if hasattr(sem, 'fecha') and sem.fecha else "Sin fecha asignada"

    comite_rows = [
        [Paragraph(
            f'<b>{docente_str(com.tutor)}</b> <font color="#64748B">(Tutor)</font> &nbsp;&nbsp;&nbsp;&nbsp; '
            f'Fecha de reunión: <b>{fecha_str}</b>',
            S['value'])],
        [Paragraph(
            f'{docente_str(com.director)} <font color="#64748B">(Director de tesis)</font>', S['value'])],
        [Paragraph(
            f'{docente_str(com.coodirector)} <font color="#64748B">(Codirector de tesis)</font>', S['value'])],
        [Paragraph(
            f'{docente_str(com.asesor)} <font color="#64748B">(Asesor de tesis)</font>', S['value'])],
    ]
    story.append(_box_table(comite_rows))

    # ── Secciones de evaluación ───────────────────────────────
    def seccion(titulo, contenido):
        story.append(Paragraph(titulo, S['section']))
        story.append(_box_table([[Paragraph(contenido or '—', S['body'])]]))

    seccion(
        'EVALUACIÓN DEL COMITÉ TUTOR SOBRE EL DESEMPENO DEL ESTUDIANTE:',
        formulario.el_comite_encuentra)
    seccion('OBSERVACIONES/RECOMENDACIONES DEL COMITÉ:',
            formulario.observaciones)
    seccion('DICTAMEN:', formulario.dictamen)
    seccion('PLAN DE TRABAJO PROPUESTO:',
            formulario.propuestas)

    # ── Calificaciones ────────────────────────────────────────
    story.append(Paragraph('CALIFICACIONES', S['section']))

    def fmt(v):
        return str(v) if v is not None else '—'

    calif_rows = [
        [Paragraph('<b>Docente</b>', S['label']),
         Paragraph('<b>Rol</b>', S['label']),
         Paragraph('<b>Calificación</b>', S['label'])],
        [Paragraph(docente_str(com.tutor), S['value']),
         Paragraph('Tutor', S['value']),
         Paragraph(fmt(formulario.calificacion_tutor), S['value'])],
        [Paragraph(docente_str(com.director), S['value']),
         Paragraph('Director', S['value']),
         Paragraph(fmt(formulario.calificacion_director), S['value'])],
        [Paragraph(docente_str(com.coodirector), S['value']),
         Paragraph('Coodirector', S['value']),
         Paragraph(fmt(formulario.calificacion_coodirector), S['value'])],
        [Paragraph(docente_str(com.asesor), S['value']),
         Paragraph('Asesor', S['value']),
         Paragraph(fmt(formulario.calificacion_asesor), S['value'])],
        [Paragraph('<b>Calificación final (promedio)</b>', S['label']),
         Paragraph('', S['value']),
         Paragraph(f'<b>{fmt(formulario.calificacion_final)}</b>', S['label'])],
    ]
    t_calif = Table(calif_rows, colWidths=[9 * cm, 3.8 * cm, 3.8 * cm])
    t_calif.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ('BACKGROUND', (0, 0), (-1, 0), BG_SOFT),
        ('BACKGROUND', (0, 5), (-1, 5), BG_SOFT),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_calif)

    # ── Firmas ────────────────────────────────────────────────
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.6, color=GOLD_ACCENT, spaceAfter=2, spaceBefore=2))
    story.append(Paragraph('VISTO BUENO Y FIRMAS DEL SÍNODO', S['section']))

    def firma_cell(docente, firmado, rol_lbl):
        celda_contenido = []

        if firmado and docente and getattr(docente, 'firma', None):
            try:
                ruta_firma = docente.firma.path
                if os.path.exists(ruta_firma):
                    img = Image(ruta_firma, width=2.4 * cm, height=0.7 * cm)
                    img.hAlign = 'CENTER'
                    celda_contenido.append(img)
                else:
                    celda_contenido.append(
                        Paragraph("<font color='#B38E46'>[APROBADO]</font>", S['firma_nombre']))
            except Exception:
                celda_contenido.append(
                    Paragraph("<font color='#B38E46'>[APROBADO]</font>", S['firma_nombre']))
        else:
            celda_contenido.append(Spacer(1, 0.7 * cm))

        celda_contenido.append(Paragraph('___________________', S['firma_nombre']))
        
        nombre_docente = f'<b>{docente.nombre} {docente.apellido_paterno}</b>' if docente else "—"
        celda_contenido.append(Paragraph(nombre_docente, S['firma_nombre']))
        celda_contenido.append(Paragraph(rol_lbl, S['firma_rol']))
        return celda_contenido

    col_w = 4.1 * cm
    firmas = Table([[
        firma_cell(com.tutor,       formulario.firma_tutor,       'Tutor'),
        firma_cell(com.director,    formulario.firma_director,    'Director'),
        firma_cell(com.coodirector, formulario.firma_coodirector, 'Codirector'),
        firma_cell(com.asesor,      formulario.firma_asesor,      'Asesor'),
    ]], colWidths=[col_w, col_w, col_w, col_w])

    firmas.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING',    (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(firmas)

    # Compilar en memoria
    doc.build(story)
    pdf_contenido_bytes = buf.getvalue()
    buf.close()

    # ── Fusión ESTRICTA a 1 sola hoja con la plantilla ─────────────────
    ruta_plantilla = os.path.join(
        settings.BASE_DIR, 'lumat_app', 'static', 'pdf', 'hoja membretada U_ACADEM_doc_digitales.pdf'
    )

    if not os.path.exists(ruta_plantilla):
        return pdf_contenido_bytes

    reader_plantilla = PdfReader(ruta_plantilla)
    reader_contenido = PdfReader(io.BytesIO(pdf_contenido_bytes))
    writer = PdfWriter()

    # Extraemos estricta y únicamente la primera página de ambos PDFs
    pagina_fondo = reader_plantilla.pages[0]
    pagina_contenido = reader_contenido.pages[0]

    # Superposición
    pagina_fondo.merge_page(pagina_contenido)
    writer.add_page(pagina_fondo)

    salida_buf = io.BytesIO()
    writer.write(salida_buf)
    pdf_final = salida_buf.getvalue()
    salida_buf.close()

    return pdf_final