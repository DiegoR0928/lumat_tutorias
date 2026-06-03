from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.http import HttpResponse, Http404

from .models import Seminario, FormularioComite
from .utils_pdf_comite import generar_pdf_comite
import io
import zipfile
from django.http import HttpResponse
from django.utils.text import slugify
from django.db.models import Q
from datetime import date
import os
from .forms import (
    FirmaCalificacionForm,
    FormularioComiteForm,
)


def es_docente(user):
    return user.groups.filter(name='Docente').exists()


def _obtener_universo_seminarios(docente):
    """Filtra y devuelve los queries base optimizados como tutor y miembro."""
    base_qs = Seminario.objects.select_related(
        'alumno', 'comite', 'formulario_comite'
    )
    como_tutor = base_qs.filter(comite__tutor=docente)
    como_miembro = base_qs.filter(
        Q(comite__miembro1=docente) | Q(comite__miembro2=docente)
    ).distinct()

    return como_tutor, como_miembro


def _combinar_roles(tutores, miembros):
    """Une listas de tutores y miembros evitando duplicados basados en pk."""
    ids_tutor = {i['seminario'].pk for i in tutores}
    miembros_unicos = [
        m for m in miembros if m['seminario'].pk not in ids_tutor
    ]
    return sorted(
        tutores + miembros_unicos,
        key=lambda i: (i['seminario'].numero, i['seminario'].periodo)
    )


def _filtrar_por_busqueda(como_tutor, como_miembro, query):
    """Flujo A: Filtra por matrícula ignorando el resto de los filtros."""
    condicion = Q(alumno__matricula__icontains=query)

    tutores_list = [
        {'seminario': s, 'rol': 'tutor'}
        for s in como_tutor.filter(condicion)
    ]
    miembros_list = [
        {'seminario': s, 'rol': 'miembro'}
        for s in como_miembro.filter(condicion)
    ]

    return _combinar_roles(tutores_list, miembros_list)


def _obtener_estado_formulario(seminario):
    """Determina de forma segura el estado general del formulario."""
    if hasattr(seminario, 'formulario_comite') and seminario.formulario_comite:
        return seminario.formulario_comite.estado_general
    return 'pendiente'


def _filtrar_por_rol_y_estado(como_tutor, como_miembro, rol, estado):
    """Flujo B: Filtra según los dropdowns de control de la pantalla."""
    tutores = [{'seminario': s, 'rol': 'tutor'} for s in como_tutor]
    miembros = [{'seminario': s, 'rol': 'miembro'} for s in como_miembro]

    if rol == 'tutor':
        seminarios_raw = tutores
    elif rol == 'miembro':
        seminarios_raw = miembros
    else:
        seminarios_raw = _combinar_roles(tutores, miembros)

    resultado = []
    for item in seminarios_raw:
        est_form = _obtener_estado_formulario(item['seminario'])

        if estado == 'completados' and est_form == 'completo':
            resultado.append(item)
        elif estado == 'pendientes' and est_form == 'pendiente':
            resultado.append(item)
        elif estado == 'todos':
            resultado.append(item)

    return resultado


def _obtener_proximos_seminarios(docente):
    """Genera de forma limpia el panel de recordatorios independientes."""
    hoy = date.today()

    # Creamos la condición OR usando el conector nativo de Django, sin operadores lógicos sueltos
    condicion_docente = (
        Q(comite__tutor=docente) |
        Q(comite__miembro1=docente) |
        Q(comite__miembro2=docente)
    )

    proximos_raw = Seminario.objects.filter(
        condicion_docente,
        fecha__gte=hoy
    ).select_related('comite').order_by('fecha', 'hora').distinct()

    proximos = []
    for s in proximos_raw:
        if _obtener_estado_formulario(s) == 'pendiente':
            rol_label = 'Tutor' if s.comite.tutor == docente else 'Miembro'
            proximos.append({'seminario': s, 'rol': rol_label})

    return proximos


@login_required
@user_passes_test(es_docente)
def docente_seminarios(request):
    docente = request.user.docente

    # Capturar parámetros
    rol = request.GET.get('rol', 'todos')
    estado = request.GET.get('estado', 'pendientes')
    query_busqueda = request.GET.get('q', '').strip()

    como_tutor, como_miembro = _obtener_universo_seminarios(docente)

    if query_busqueda:
        seminarios = _filtrar_por_busqueda(
            como_tutor, como_miembro, query_busqueda
        )
        rol = 'todos'
        estado = 'todos'
    else:
        seminarios = _filtrar_por_rol_y_estado(
            como_tutor, como_miembro, rol, estado
        )

    return render(request, 'docente_seminario.html', {
        'docente': docente,
        'seminarios': seminarios,
        'proximos_seminarios': _obtener_proximos_seminarios(docente),
        'rol_activo': rol,
        'estado_activo': estado,
        'query_busqueda': query_busqueda,
    })

# ── Helpers ───────────────────────────────────────────────────


def _rol_en_seminario(docente, seminario):
    """Devuelve 'tutor', 'miembro1', 'miembro2' o None."""
    c = seminario.comite
    if c.tutor == docente:
        return 'tutor'
    if c.miembro1 == docente:
        return 'miembro1'
    if c.miembro2 == docente:
        return 'miembro2'
    return None


def _get_o_crear_formulario(seminario):
    f, _ = FormularioComite.objects.get_or_create(seminario=seminario)
    return f


# ── Vista principal de detalle ────────────────────────────────

@login_required
@user_passes_test(es_docente)
def docente_seminario_detalle(request, seminario_id):
    docente = request.user.docente
    seminario = get_object_or_404(
        Seminario.objects.select_related(
            'alumno', 'comite',
            'comite__tutor', 'comite__miembro1', 'comite__miembro2'
        ).prefetch_related('evidencias'),
        pk=seminario_id
    )

    rol = _rol_en_seminario(docente, seminario)
    # if not rol:
    #     raise Http404

    formulario = _get_o_crear_formulario(seminario)
    rol_activo = request.GET.get('rol', 'todos')

    # ── POST: tutor guarda el contenido del informe ───────────
    if request.method == 'POST' and rol == 'tutor':
        form = FormularioComiteForm(request.POST, instance=formulario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Informe guardado correctamente.')
            return redirect(
                'lumat_app:docente_seminario_detalle', seminario_id=seminario_id)
    else:
        form = FormularioComiteForm(
            instance=formulario) if rol == 'tutor' else None

    # ── Formulario de firma / calificación ────────────────────
    ya_firme = getattr(formulario, f'firma_{rol}')
    firma_form = FirmaCalificacionForm() if not ya_firme else None

    return render(request, 'docente_seminario_detalle.html', {
        'docente': docente,
        'seminario': seminario,
        'formulario': formulario,
        'form': form,
        'firma_form': firma_form,
        'rol': rol,
        'rol_activo': rol_activo,
        'ya_firme': ya_firme,
    })

# ── Vista: firmar + calificar ─────────────────────────────────


@login_required
@user_passes_test(es_docente)
def docente_firmar_seminario(request, seminario_id):
    if request.method != 'POST':
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    docente = request.user.docente
    seminario = get_object_or_404(
        Seminario.objects.select_related(
            'comite', 'comite__tutor',
            'comite__miembro1', 'comite__miembro2'),
        pk=seminario_id)

    rol = _rol_en_seminario(docente, seminario)
    # if not rol:
    #     raise Http404

    formulario = _get_o_crear_formulario(seminario)

    if getattr(formulario, f'firma_{rol}'):
        messages.warning(request, 'Ya habías firmado este seminario.')
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    form = FirmaCalificacionForm(request.POST)
    if form.is_valid():
        calif = form.cleaned_data['calificacion']

        # Asignar calificación según rol
        campo_calif = {
            'tutor': 'calificacion_tutor',
            'miembro1': 'calificacion_miembro1',
            'miembro2': 'calificacion_miembro2',
        }[rol]
        setattr(formulario, campo_calif, calif)
        setattr(formulario, f'firma_{rol}', True)
        formulario.save()   # recalcula calificacion_final y estado_general

        messages.success(request, 'Firma y calificación registradas.')
    else:
        messages.error(request, 'Datos inválidos. Verifica la calificación.')

    return redirect('lumat_app:docente_seminario_detalle',
                    seminario_id=seminario_id)


# ── Vista: descargar PDF ──────────────────────────────────────

@login_required
@user_passes_test(es_docente)
def docente_descargar_acta(request, seminario_id):
    docente = request.user.docente
    seminario = get_object_or_404(
        Seminario.objects.select_related(
            'alumno', 'comite',
            'comite__tutor', 'comite__miembro1', 'comite__miembro2'),
        pk=seminario_id)

    if not _rol_en_seminario(docente, seminario):
        raise Http404

    formulario = get_object_or_404(FormularioComite, seminario=seminario)

    pdf_bytes = generar_pdf_comite(formulario)
    nombre = (f'acta_seminario_{seminario.numero}_'
              f'periodo_{seminario.periodo}_'
              f'{seminario.alumno.apellido_paterno}.pdf')

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response


@login_required
@user_passes_test(es_docente)
def descargar_evidencias_zip(request, seminario_id):
    seminario = get_object_or_404(Seminario, pk=seminario_id)
    evidencias = seminario.evidencias.all()

    if not evidencias:
        messages.error(
            request, "Este seminario no tiene evidencias para descargar.")
        return redirect('lumat_app:docente_seminario_detalle', seminario_id=seminario_id)

    # Crear el archivo ZIP en memoria
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for evidencia in evidencias:
            if evidencia.archivo and os.path.exists(evidencia.archivo.path):
                # Usar el nombre guardado en la BD o el nombre del archivo físico
                nombre_archivo = evidencia.nombre or os.path.basename(
                    evidencia.archivo.name)
                # Si el nombre no tiene extensión, se la agregamos de manera segura
                if not os.path.splitext(nombre_archivo)[1]:
                    ext = os.path.splitext(evidencia.archivo.name)[1]
                    nombre_archivo += ext

                zip_file.write(evidencia.archivo.path, nombre_archivo)

    # Estructurar el nombre solicitado: nombre-semestre-periodo.zip
    nombre_alumno = slugify(
        f"{seminario.alumno.nombre} {seminario.alumno.apellido_paterno}")
    alumno = seminario.alumno
    nombre_zip = f"{nombre_alumno}-semestre{alumno.semestre}-{slugify(seminario.periodo)}.zip"

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
    return response
