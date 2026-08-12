# utils_pdf_comite.py — coloca este archivo en lumat_app/utils_pdf_comite.py
"""Genera el PDF del Informe Semestral del Comité Tutor sobre una plantilla membretada."""

import io
import os
from django.conf import settings
from pypdf import PdfReader, PdfWriter

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image,
)
from reportlab.lib.enums import TA_CENTER

# ── Paleta ────────────────────────────────────────────────────
TEAL = colors.HexColor('#4a7c7a')
WARM = colors.HexColor('#4a3f32')
LIGHT = colors.HexColor('#eee8de')
BORDER = colors.HexColor('#c8b89a')
WHITE = colors.white
BLACK = colors.black


def _styles():
    s = {}

    s['titulo'] = ParagraphStyle(
        'titulo', fontName='Times-Bold',
        fontSize=15, leading=18, alignment=TA_CENTER, textColor=WARM)

    s['subtitulo'] = ParagraphStyle(
        'subtitulo', fontName='Times-Roman',
        fontSize=10, leading=13, alignment=TA_CENTER, textColor=WARM)

    s['label'] = ParagraphStyle(
        'label', fontName='Times-Bold',
        fontSize=8, leading=11, textColor=WARM)

    s['value'] = ParagraphStyle(
        'value', fontName='Times-Roman',
        fontSize=9, leading=12, textColor=WARM)

    s['section'] = ParagraphStyle(
        'section', fontName='Times-Bold',
        fontSize=8, leading=11, textColor=TEAL,
        spaceAfter=4)

    s['body'] = ParagraphStyle(
        'body', fontName='Times-Roman',
        fontSize=9, leading=13, textColor=WARM)

    s['firma_nombre'] = ParagraphStyle(
        'firma_nombre', fontName='Times-Roman',
        fontSize=8, leading=11, alignment=TA_CENTER, textColor=WARM)

    return s


def _hr():
    return HRFlowable(width='100%', thickness=0.5,
                      color=BORDER, spaceAfter=6, spaceBefore=6)


def _box_table(content_rows, style_extra=None):
    """Crea una tabla con borde exterior fino color crema."""
    base_style = [
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    if style_extra:
        base_style += style_extra
    t = Table(content_rows, colWidths=['100%'])
    t.setStyle(TableStyle(base_style))
    return t


def generar_pdf_comite(formulario) -> bytes:
    """Recibe una instancia de FormularioComite con .seminario pre-cargado.

    Devuelve los bytes del PDF montado sobre la plantilla membretada.
    """
    buf = io.BytesIO()
    
    # ── Ajuste de márgenes para no solapar el membrete ────────────────────
    # Ajustamos topMargin y bottomMargin para dejar espacio a los logotipos y al pie de página.
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=3.8 * cm, bottomMargin=3.2 * cm,
    )
    S = _styles()
    sem = formulario.seminario
    al = sem.alumno
    com = sem.comite
    story = []

    # ── Encabezado del Acta ──────────────────────────────────────────────
    story.append(Paragraph('INFORME SEMESTRAL DEL COMITÉ TUTOR', S['titulo']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'Semestre: {sem.numero}', S['subtitulo']))
    story.append(Spacer(1, 6))
    story.append(_hr())

    # ── Datos del alumno ──────────────────────────────────────
    story.append(Paragraph('ALUMNO/A', S['section']))

    alumno_data = [
        [Paragraph(
            f'<b>Nombre:</b> {al.nombre} {al.apellido_paterno} {al.apellido_materno}', S['value'])],
        [Paragraph(
            f'<b>Matrícula:</b> {al.matricula or "—"} &nbsp;&nbsp; '
            f'<b>Semestre:</b> {al.semestre} &nbsp;&nbsp; '
            f'<b>Correo:</b> {al.correo}', S['value'])],
    ]
    story.append(_box_table(alumno_data))
    story.append(Spacer(1, 8))

    # ── Comité ────────────────────────────────────────────────
    story.append(Paragraph('COMITÉ TUTOR', S['section']))

    def docente_str(d):
        if not d:
            return "—"
        return f'{d.nombre} {d.apellido_paterno} {d.apellido_materno}'

    fecha_str = sem.fecha.strftime("%d-%m-%Y") if hasattr(sem, 'fecha') and sem.fecha else "Sin fecha asignada"

    comite_rows = [
        [Paragraph(
            f'<b>{docente_str(com.tutor)}</b> (Tutor) &nbsp;&nbsp;&nbsp; '
            f'Fecha de reunión: <b>{fecha_str}</b>',
            S['value'])],
        [Paragraph(
            f'{docente_str(com.director)} (Director de tesis)', S['value'])],
        [Paragraph(
            f'{docente_str(com.coodirector)} (Codirector de tesis)', S['value'])],
        [Paragraph(
            f'{docente_str(com.asesor)} (Asesor de tesis)', S['value'])],
    ]
    story.append(_box_table(comite_rows))
    story.append(Spacer(1, 8))

    # ── Secciones de evaluación ───────────────────────────────
    def seccion(titulo, contenido):
        story.append(Paragraph(titulo, S['section']))
        story.append(_box_table([[Paragraph(contenido or '—', S['body'])]]))
        story.append(Spacer(1, 6))

    seccion(
        'TRAS UNA CUIDADOSA EVALUACIÓN, ESTE COMITÉ TUTOR ENCUENTRA QUE EL ESTUDIANTE:',
        formulario.el_comite_encuentra)
    seccion('OTROS ASPECTOS OBSERVADOS POR ESTE COMITÉ:',
            formulario.observaciones)
    seccion('DICTAMEN:', formulario.dictamen)
    seccion('PROPONEMOS QUE EL ESTUDIANTE SIGA EL SIGUIENTE PLAN DE TRABAJO:',
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
    t = Table(calif_rows, colWidths=[9 * cm, 3.5 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('BACKGROUND', (0, 5), (-1, 5), LIGHT),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # ── Firmas ────────────────────────────────────────────────
    story.append(Paragraph('VISTO BUENO', S['section']))
    story.append(Spacer(1, 4))

    def firma_cell(docente, firmado):
        celda_contenido = []
        if firmado and docente and getattr(docente, 'firma', None):
            try:
                ruta_firma = docente.firma.path
                if os.path.exists(ruta_firma):
                    img = Image(ruta_firma, width=2.8 * cm, height=1.2 * cm)
                    img.hAlign = 'CENTER'
                    celda_contenido.append(img)
                else:
                    celda_contenido.append(
                        Paragraph("<font color='#a89880'>[APROBADO]</font>", S['firma_nombre']))
            except Exception:
                celda_contenido.append(
                    Paragraph("<font color='#a89880'>[APROBADO]</font>", S['firma_nombre']))
        else:
            celda_contenido.append(Spacer(1, 0.8 * cm))
            celda_contenido.append(Paragraph('___________________', S['firma_nombre']))

        celda_contenido.append(Spacer(1, 4))
        nombre_str = f'<b>{docente.nombre} {docente.apellido_paterno}</b>' if docente else "—"
        celda_contenido.append(Paragraph(nombre_str, S['firma_nombre']))
        return celda_contenido

    col_w = 3.8 * cm
    firmas = Table([[
        firma_cell(com.tutor, formulario.firma_tutor),
        firma_cell(com.director, formulario.firma_director),
        firma_cell(com.coodirector, formulario.firma_coodirector),
        firma_cell(com.asesor, formulario.firma_asesor),
    ]], colWidths=[col_w, col_w, col_w, col_w])

    firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(firmas)

    # Generar el PDF transparente en memoria
    doc.build(story)
    pdf_contenido_bytes = buf.getvalue()
    buf.close()

    # ── Fusión de la plantilla con el contenido ─────────────────────────
    # Ruta del archivo de plantilla (coloca la plantilla en tus static o templates)
    ruta_plantilla = os.path.join(
        settings.BASE_DIR, 'lumat_app', 'static', 'pdf', 'hoja membretada U_ACADEM_doc_digitales.pdf'
    )

    if not os.path.exists(ruta_plantilla):
        # Si no existe la plantilla, se devuelve solo el contenido generado sin fallar
        return pdf_contenido_bytes

    reader_plantilla = PdfReader(ruta_plantilla)
    pagina_plantilla = reader_plantilla.pages[0]

    reader_contenido = PdfReader(io.BytesIO(pdf_contenido_bytes))
    writer = PdfWriter()

    # Para cada página generada por ReportLab, clonar la plantilla y superponer el contenido
    for pagina_contenido in reader_contenido.pages:
        # Copiamos la plantilla para no alterar la página original
        pagina_fondo = reader_plantilla.pages[0]
        # Superponemos la capa de texto sobre la plantilla
        pagina_fondo.merge_page(pagina_contenido)
        writer.add_page(pagina_fondo)

    salida_buf = io.BytesIO()
    writer.write(salida_buf)
    pdf_final = salida_buf.getvalue()
    salida_buf.close()

    return pdf_final