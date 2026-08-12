# lumat_app/acta_generator.py
# Genera el acta semestral del alumno en PDF usando reportlab y un fondo membretado institucional.

import os
from io import BytesIO
from django.conf import settings

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from pypdf import PdfReader, PdfWriter


# ── Paleta Institucional (UAZ / LUMAT) ────────────────────────
NAVY_PRIMARY = colors.HexColor("#1A2B4C")  # Azul marino institucional
GOLD_ACCENT  = colors.HexColor("#B38E46")  # Dorado/Bronce decorativo
BG_SOFT      = colors.HexColor("#F8FAFC")  # Fondo limpio ligeramente gris
BORDER_SOFT  = colors.HexColor("#CBD5E1")  # Borde suave pero definido
TEXT_MAIN    = colors.HexColor("#1E293B")  # Texto oscuro legible
TEXT_MUTED   = colors.HexColor("#64748B")  # Texto secundario


def generar_acta_alumno(seminario, alumno, comite, datos_form, ruta_fondo=None):
    """
    Genera el acta del alumno asegurando 1 página bien distribuida,
    armonizada con la hoja membretada UAZ/LUMAT sin recuadros pesados en el título.
    Muestra únicamente las firmas del Director y Codirector.
    """
    buffer_reportlab = BytesIO()

    # Márgenes ajustados para aprovechar la hoja y respetar el membrete
    doc = SimpleDocTemplate(
        buffer_reportlab,
        pagesize=letter,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=3.6 * cm,    # Espacio libre para logotipos membretados
        bottomMargin=2.2 * cm, # Espacio libre para dirección/contacto
    )

    styles = getSampleStyleSheet()

    # ── Estilos Tipográficos ──────────────────────────────────
    titulo_style = ParagraphStyle(
        "titulo_acta", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold",
        textColor=NAVY_PRIMARY, alignment=TA_CENTER, leading=14,
    )
    subtitulo_style = ParagraphStyle(
        "subtitulo_acta", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        textColor=TEXT_MUTED, alignment=TA_CENTER, leading=10,
    )
    seccion = ParagraphStyle(
        "seccion", parent=styles["Normal"],
        fontSize=8.5, fontName="Helvetica-Bold",
        textColor=NAVY_PRIMARY, spaceBefore=6, spaceAfter=3,
    )
    normal = ParagraphStyle(
        "normal_lumat", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        leading=11, textColor=TEXT_MAIN,
    )
    rol_style = ParagraphStyle(
        "rol", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica-Bold",
        textColor=TEXT_MUTED, alignment=TA_CENTER, leading=9,
    )
    firma_nombre_style = ParagraphStyle(
        "firma_nombre", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=NAVY_PRIMARY, alignment=TA_CENTER, leading=10,
    )

    story = []
    d = datos_form

    # ── Encabezado Tipográfico Limpio (Sin Cuadro) ───────────
    if seminario.fecha:
        semestre_label = (
            seminario.fecha.strftime("%Y")
            + f"-{seminario.fecha.month // 7 + 1}"
        )
        fecha_str = seminario.fecha.strftime("%d/%m/%Y")
    else:
        semestre_label = "Sin fecha"
        fecha_str = "Sin fecha asignada"

    story.append(Paragraph("INFORME SEMESTRAL DEL ALUMNO", titulo_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        f"Seminario {seminario.numero} &nbsp;·&nbsp; Periodo {semestre_label} &nbsp;·&nbsp; Fecha: {fecha_str}",
        subtitulo_style
    ))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=0.8, color=GOLD_ACCENT, spaceAfter=6, spaceBefore=2))

    # ── Datos del Alumno ─────────────────────────────────────
    story.append(Paragraph("DATOS DEL ALUMNO/A", seccion))
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
    ], colWidths=["52%", "48%"])
    t_alumno.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ("BACKGROUND",    (0, 0), (-1, -1), BG_SOFT),
        ("TOPPADDING",    (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
    ]))
    story.append(t_alumno)

    # ── Comité Tutor ─────────────────────────────────────────
    story.append(Paragraph("COMITÉ TUTOR Y SEGUIMIENTO", seccion))

    def nd(doc_obj):
        if not doc_obj:
            return "—"
        return f"{doc_obj.nombre} {doc_obj.apellido_paterno} {doc_obj.apellido_materno}"

    t_comite = Table([
        [
            Paragraph(f"<b>{nd(comite.tutor)}</b> <font color='#64748B'>( Tutor )</font>", normal),
            Paragraph(f"Reuniones con tutor: <b>{d.get('reuniones_tutor', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.director)}</b> <font color='#64748B'>( Director )</font>", normal),
            Paragraph(f"Reuniones con comité: <b>{d.get('reuniones_comite', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.coodirector)}</b> <font color='#64748B'>( Coodirector )</font>", normal),
            Paragraph(f"Asistencias al Coloquio: <b>{d.get('coloquios', 0)}</b>", normal),
        ],
        [
            Paragraph(f"<b>{nd(comite.asesor)}</b> <font color='#64748B'>( Asesor )</font>", normal),
            Paragraph("", normal),
        ],
    ], colWidths=["58%", "42%"])
    t_comite.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ("BACKGROUND",    (0, 0), (-1, -1), BG_SOFT),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
    ]))
    story.append(t_comite)

    # ── Secciones de Actividades ─────────────────────────────
    def _caja_compacta(texto):
        return _caja(texto, normal, padding=3.5)

    story.append(Paragraph("ACTIVIDAD PRINCIPAL DURANTE EL SEMESTRE", seccion))
    story.append(_caja_compacta(d.get("actividad_principal", "—")))

    story.append(Paragraph("CURSOS ACREDITADOS", seccion))
    story.append(_caja_compacta(d.get("cursos") or "No inscribí ningún curso."))

    story.append(Paragraph("ARTÍCULOS ENVIADOS / PUBLICADOS", seccion))
    story.append(_caja_compacta(d.get("articulos") or "No tengo artículos enviados o publicados."))

    story.append(Paragraph("EVENTOS ACADÉMICOS / ESTANCIAS DE INVESTIGACIÓN", seccion))
    story.append(_caja_compacta(d.get("eventos") or "No asistí a ningún evento ni realicé alguna estancia."))

    story.append(Paragraph("PLAN DE ACTIVIDADES PARA EL SIGUIENTE SEMESTRE", seccion))
    story.append(_caja_compacta(d.get("plan_siguiente", "—")))

    coment = d.get("comentarios", "").strip()
    if coment:
        story.append(Paragraph("COMENTARIOS ADICIONALES", seccion))
        story.append(_caja_compacta(coment))

    # ── Firmas (Exclusivo Director y Codirector) ──────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.6, color=GOLD_ACCENT, spaceAfter=4, spaceBefore=2))
    story.append(Paragraph("VISTO BUENO DEL DIRECTOR/CODIRECTOR", seccion))

    def _celda_firma(docente_obj, rol_label):
        celda = []
        if docente_obj and getattr(docente_obj, 'firma', None):
            try:
                ruta = docente_obj.firma.path
                if os.path.exists(ruta):
                    img = Image(ruta, width=2.6 * cm, height=0.9 * cm)
                    img.hAlign = "CENTER"
                    celda.append(img)
                else:
                    celda.append(Spacer(1, 0.9 * cm))
            except Exception:
                celda.append(Spacer(1, 0.9 * cm))
        else:
            celda.append(Spacer(1, 0.9 * cm))

        celda.append(Paragraph("_____________________________", firma_nombre_style))
        celda.append(Spacer(1, 2))
        
        nombre_str = f"{docente_obj.nombre} {docente_obj.apellido_paterno} {docente_obj.apellido_materno}" if docente_obj else "—"
        celda.append(Paragraph(nombre_str, firma_nombre_style))
        celda.append(Paragraph(rol_label, rol_style))
        return celda

    miembros_firma = [
        (comite.director, "Director de Tesis"),
        (comite.coodirector, "Codirector de Tesis"),
    ]

    t_firmas = Table(
        [[_celda_firma(doc_obj, rol_lbl) for doc_obj, rol_lbl in miembros_firma]],
        colWidths=["50%", "50%"],
    )
    t_firmas.setStyle(TableStyle([
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_firmas)

    # Construir PDF en memoria
    doc.build(story)
    buffer_reportlab.seek(0)

    # ── Superposición con el fondo membretado ─────────────────
    if not ruta_fondo:
        if hasattr(settings, 'BASE_DIR'):
            ruta_fondo = os.path.join(
                settings.BASE_DIR, "lumat_app", "static", "pdf", "hoja membretada U_ACADEM_doc_digitales.pdf"
            )
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_fondo = os.path.join(
                base_dir, "static", "pdf", "hoja membretada U_ACADEM_doc_digitales.pdf"
            )

    if not os.path.exists(ruta_fondo):
        ruta_fondo = "static/pdf/hoja membretada U_ACADEM_doc_digitales.pdf"

    if os.path.exists(ruta_fondo):
        reader_fondo = PdfReader(ruta_fondo)
        reader_contenido = PdfReader(buffer_reportlab)
        writer = PdfWriter()

        pagina_fondo = reader_fondo.pages[0]
        pagina_contenido = reader_contenido.pages[0]

        # Fusiona el contenido del acta sobre la hoja de fondo
        pagina_fondo.merge_page(pagina_contenido)
        writer.add_page(pagina_fondo)

        buffer_final = BytesIO()
        writer.write(buffer_final)
        buffer_final.seek(0)
        return buffer_final
    else:
        print(f"[ADVERTENCIA] No se encontró la hoja membretada en: {ruta_fondo}")
        return buffer_reportlab


def _caja(texto, style, padding=3.5):
    t = Table(
        [[Paragraph(str(texto) if texto else "—", style)]],
        colWidths=["100%"],
    )
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_SOFT),
        ("BACKGROUND",    (0, 0), (-1, -1), BG_SOFT),
        ("TOPPADDING",    (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]))
    return t