from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from weasyprint import HTML
from datetime import datetime, timedelta, time
import random
from django.core.files.base import ContentFile
from django.http import HttpResponse, Http404

from .models import Seminario, FormularioComite
from .utils_pdf_comite import generar_pdf_comite
import io
import zipfile
from django.http import HttpResponse
from django.utils.text import slugify
from django.db.models import Q
from datetime import date

from .models import (
    Evidencia,
    SolicitudCambioTutor
)
from .forms import (
    FirmaCalificacionForm,
    FormularioComiteForm,
)


def es_docente(user):
    return user.groups.filter(name='Docente').exists()


@login_required
@user_passes_test(es_docente)
def docente_seminarios(request):
    docente = request.user.docente

    # Capturar parámetros
    rol = request.GET.get('rol', 'todos')
    estado = request.GET.get('estado', 'pendientes')
    query_busqueda = request.GET.get('q', '').strip()

    # Todo tu universo base de seminarios (Tutor + Miembro)
    como_tutor = Seminario.objects.filter(
        comite__tutor=docente
    ).select_related('alumno', 'comite', 'formulario_comite')

    como_miembro = Seminario.objects.filter(
        comite__miembro1=docente
    ).select_related('alumno', 'comite', 'formulario_comite') | Seminario.objects.filter(
        comite__miembro2=docente
    ).select_related('alumno', 'comite', 'formulario_comite')

    seminarios = []

    # 1. FLUJO A: Si el usuario escribe una matrícula, busca en TODO sin importar los filtros
    if query_busqueda:
        condicion_matricula = Q(alumno__matricula__icontains=query_busqueda)

        tutores_filtrados = como_tutor.filter(condicion_matricula)
        miembros_filtrados = como_miembro.distinct().filter(condicion_matricula)

        tutores_list = [{'seminario': s, 'rol': 'tutor'}
                        for s in tutores_filtrados]
        miembros_list = [{'seminario': s, 'rol': 'miembro'}
                         for s in miembros_filtrados]

        ids_tutor = {i['seminario'].pk for i in tutores_list}
        miembros_list = [
            i for i in miembros_list if i['seminario'].pk not in ids_tutor]

        seminarios = sorted(
            tutores_list + miembros_list,
            key=lambda i: (i['seminario'].numero, i['seminario'].periodo)
        )

        # Forzamos los estados visuales del dropdown a 'todos' para que coincida con la pantalla
        rol = 'todos'
        estado = 'todos'

    # 2. FLUJO B: Si no hay búsqueda, funciona el comportamiento por defecto (Pendientes de cualquier rol)
    else:
        if rol == 'tutor':
            seminarios_raw = [{'seminario': s, 'rol': 'tutor'}
                              for s in como_tutor]
        elif rol == 'miembro':
            seminarios_raw = [{'seminario': s, 'rol': 'miembro'}
                              for s in como_miembro.distinct()]
        else:
            tutores = [{'seminario': s, 'rol': 'tutor'} for s in como_tutor]
            miembros = [{'seminario': s, 'rol': 'miembro'}
                        for s in como_miembro.distinct()]
            ids_tutor = {i['seminario'].pk for i in tutores}
            miembros = [
                i for i in miembros if i['seminario'].pk not in ids_tutor]
            seminarios_raw = tutores + miembros

        for item in sorted(seminarios_raw, key=lambda i: (i['seminario'].numero, i['seminario'].periodo)):
            sem = item['seminario']
            estado_form = 'pendiente'
            if hasattr(sem, 'formulario_comite') and sem.formulario_comite:
                estado_form = sem.formulario_comite.estado_general

            if estado == 'completados' and estado_form == 'completo':
                seminarios.append(item)
            elif estado == 'pendientes' and estado_form == 'pendiente':
                seminarios.append(item)
            elif estado == 'todos':
                seminarios.append(item)

    # --- PANEL DE RECORDATORIOS (Independiente) ---
    hoy = date.today()
    todos_mis_seminarios = (Seminario.objects.filter(comite__tutor=docente) |
                            Seminario.objects.filter(comite__miembro1=docente) |
                            Seminario.objects.filter(comite__miembro2=docente)).distinct()

    proximos_raw = todos_mis_seminarios.filter(
        fecha__gte=hoy).order_by('fecha', 'hora')
    proximos_seminarios = []
    for s in proximos_raw:
        est_form = 'pendiente'
        if hasattr(s, 'formulario_comite') and s.formulario_comite:
            est_form = s.formulario_comite.estado_general
        if est_form == 'pendiente':
            r_label = 'Tutor' if s.comite.tutor == docente else 'Miembro'
            proximos_seminarios.append({'seminario': s, 'rol': r_label})

    return render(request, 'docente_seminario.html', {
        'docente': docente,
        'seminarios': seminarios,
        'proximos_seminarios': proximos_seminarios,
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
        ).prefetch_related('evidencias'),  # 👈 AQUÍ: Precarga todas las evidencias asociadas
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
        'docente':      docente,
        'seminario':    seminario,
        'formulario':   formulario,
        'form':         form,
        'firma_form':   firma_form,
        'rol':          rol,
        'rol_activo':   rol_activo,
        'ya_firme':     ya_firme,
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
            'tutor':    'calificacion_tutor',
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
    nombre_zip = f"{nombre_alumno}-semestre{seminario.alumno.semestre}-{slugify(seminario.periodo)}.zip"

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
    return response
