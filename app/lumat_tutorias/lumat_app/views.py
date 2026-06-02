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

from .models import Alumno, Docente, Seminario, CalendarioGenerado, Comite, FormularioComite
from django.utils import timezone
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
    UserForm,
    AlumnoForm,
    AlumnoEditForm,
    PasswordChangeCustomForm,
)

# ==========================================
# 1. AUTENTICACIÓN Y ACCESO
# ==========================================


class CustomLoginView(LoginView):
    """Maneja el inicio de sesión y redirige según el rol del usuario."""
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user

        # Prioridad para superusuarios o staff para ir al admin de Unfold
        if user.is_superuser or user.is_staff:
            return '/admin/'

        # Redirección por grupos
        if user.groups.filter(name='Docente').exists():
            return reverse('lumat_app:docente_seminarios')
        elif user.groups.filter(name='Alumno').exists():
            semestre = int(user.alumno.semestre)
            return reverse(
                'lumat_app:seminario_detalle',
                kwargs={'num': semestre}
            )

        return '/'


class CustomLogoutView(LogoutView):
    """Cierra la sesión y redirige al login."""
    next_page = 'lumat_app:login'


# def es_docente(user):
#     return user.groups.filter(name='Docente').exists()


def es_alumno(user):
    return user.groups.filter(name='Alumno').exists()

# ==========================================
# 2. VISTAS DE REGISTRO Y DASHBOARDS
# ==========================================


def registro(request):
    """Registra un nuevo usuario y lo vincula a un perfil de Alumno."""
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        alumno_form = AlumnoForm(request.POST)

        if user_form.is_valid() and alumno_form.is_valid():
            # Crear el usuario
            user = user_form.save(commit=False)
            user.first_name = alumno_form.cleaned_data.get('nombre', '')
            user.last_name = alumno_form.cleaned_data.get(
                'apellido_paterno', '')
            user.set_password(user_form.cleaned_data['password'])

            user.save()

            # Asignar grupo (get_or_create previene errores si el grupo
            # no existe)
            grupo, _ = Group.objects.get_or_create(name='Alumno')
            user.groups.add(grupo)

            # Crear el perfil de alumno
            alumno = alumno_form.save(commit=False)
            alumno.user = user
            alumno.correo = user.email
            alumno.save()

            messages.success(request, "Alumno registrado con éxito")
            return redirect('lumat_app:login')  # Redirigir al login tras éxito
    else:
        user_form = UserForm()
        alumno_form = AlumnoForm()

    return render(request, 'registro.html', {
        'user_form': user_form,
        'alumno_form': alumno_form
    })


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_seminario_para_alumno(alumno, numero):
    """
    Devuelve el último intento (periodo más alto)
    del seminario indicado para el alumno.
    """

    return (
        Seminario.objects
        .select_related(
            'comite',
            'comite__tutor',
            'comite__miembro1',
            'comite__miembro2',
        )
        .filter(
            alumno=alumno,
            numero=numero
        )
        .order_by('-periodo')
        .first()
    )


def _proximo_seminario(alumno):
    """
    Devuelve el próximo Seminario programado (sin calificación aún)
    con fecha >= hoy, o None.
    """
    hoy = timezone.now().date()
    return (
        Seminario.objects
        .filter(alumno=alumno, calificacion__isnull=True, fecha__gte=hoy)
        .order_by('fecha', 'hora')
        .first()
    )


# ─────────────────────────────────────────────
# Vista: listado / hub de seminarios
# ─────────────────────────────────────────────

# @login_required
# def seminario(request):
#     """Redirige al seminario activo (el más reciente desbloqueado)."""
#     alumno = request.user.alumno
#     semestre = int(alumno.semestre)
#     return redirect('lumat_app:seminario_detalle', num=semestre)


# ─────────────────────────────────────────────
# Vista: detalle de un seminario
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_alumno)
def seminario_detalle(request, num):
    alumno = request.user.alumno
    semestre = int(alumno.semestre)

    # # Validaciones de acceso
    # if not (1 <= num <= 8):
    #     messages.error(request, "Número de seminario inválido.")
    #     return redirect(
    #         'lumat_app:seminario_detalle',
    #         num=semestre
    #     )

    if num > semestre:
        messages.warning(
            request,
            f"El seminario {num} estará disponible en semestres posteriores."
        )
        return redirect(
            'lumat_app:seminario_detalle',
            num=semestre
        )

    # Obtiene el último periodo de este seminario
    seminario_obj = _get_seminario_para_alumno(alumno, num)

    comite = seminario_obj.comite if seminario_obj else None

    evidencias = (
        Evidencia.objects.filter(
            seminario=seminario_obj
        ).order_by('subido_en')
        if seminario_obj else Evidencia.objects.none()
    )

    solicitud_pendiente = SolicitudCambioTutor.objects.filter(
        alumno=alumno,
        estado='pendiente'
    ).exists()

    context = {
        'alumno': alumno,
        'num': num,  # número del seminario (1-8)
        'seminario': seminario_obj,
        'comite': comite,
        'evidencias': evidencias,
        'proximo_seminario': _proximo_seminario(alumno),
        'solicitud_pendiente': solicitud_pendiente,
        'periodo': seminario_obj.periodo if seminario_obj else None,
    }

    return render(
        request,
        'alumno_seminario.html',
        context
    )


# ─────────────────────────────────────────────
# Vista: subir evidencia
# ─────────────────────────────────────────────

@login_required
def subir_evidencia(request, seminario_id):
    alumno = request.user.alumno
    seminario_obj = get_object_or_404(
        Seminario, id=seminario_id, alumno=alumno)

    if request.method != 'POST':
        return redirect('lumat_app:seminario_detalle',
                        num=seminario_obj.numero)

    archivo = request.FILES.get('archivo')
    nombre_actividad = request.POST.get('nombre', '').strip()

    if not archivo:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect('lumat_app:seminario_detalle',
                        num=seminario_obj.numero)

    # Validación de tamaño (máx. 10 MB)
    MAX_SIZE = 10 * 1024 * 1024
    if archivo.size > MAX_SIZE:
        messages.error(request, "El archivo no puede superar 10 MB.")
        return redirect('lumat_app:seminario_detalle',
                        num=seminario_obj.numero)

    # Validación de tipo MIME básica
    TIPOS_PERMITIDOS = (
        # 'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
    )
    if archivo.content_type not in TIPOS_PERMITIDOS:
        messages.error(
            request,
            "Solo se permiten imágenes y PDFs."
        )
        return redirect('lumat_app:seminario_detalle',
                        num=seminario_obj.numero)

    Evidencia.objects.create(
        seminario=seminario_obj,
        archivo=archivo,
        nombre=nombre_actividad,
    )

    messages.success(request, "Evidencia subida correctamente.")
    return redirect('lumat_app:seminario_detalle',
                    num=seminario_obj.numero)


# ─────────────────────────────────────────────
# Vista: solicitar cambio de tutor
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_alumno)
def cambio_tutor(request):
    alumno = request.user.alumno

    # 1. Buscamos si existe una solicitud pendiente
    solicitud_pendiente = SolicitudCambioTutor.objects.filter(
        alumno=alumno, estado="pendiente"
    ).first()  # Usamos .first() para obtener el objeto real o None

    # 2. Si hay una solicitud pendiente, avisamos al usuario
    if solicitud_pendiente:
        messages.warning(
            request,
            "Ya tienes una solicitud de cambio de tutor en proceso. "
            "No puedes enviar una nueva hasta que esta se resuelva.",
        )

    if request.method == "POST":
        # Segurito: Si intentan saltarse el bloqueo del HTML enviando un
        # POST manual, los frenamos aquí si ya existe una solicitud pendiente.
        if solicitud_pendiente:
            messages.error(request, "No puedes enviar otra solicitud.")
            return redirect(
                "lumat_app:seminario_detalle",
                num=int(alumno.semestre)
            )

        motivo = request.POST.get("motivo", "").strip()
        if not motivo:
            messages.error(
                request, "Debes indicar el motivo de la solicitud."
            )
        else:
            SolicitudCambioTutor.objects.create(alumno=alumno, motivo=motivo)
            messages.success(
                request,
                "Solicitud enviada. La coordinación la revisará pronto.",
            )
            return redirect(
                "lumat_app:seminario_detalle", num=int(alumno.semestre)
            )

    # 3. Pasamos 'solicitud_pendiente' al contexto del template
    return render(
        request,
        "alumno_cambio_tutor.html",
        {
            "alumno": alumno,
            "solicitud_pendiente": solicitud_pendiente
        }
    )


# @user_passes_test(es_docente)
# def docente_dashboard(request):
#     return render(request, 'docente_dashboard.html')


# @login_required
# @user_passes_test(es_docente)
# def docente_seminarios(request):
#     docente = request.user.docente

#     # Capturar parámetros
#     rol = request.GET.get('rol', 'todos')
#     estado = request.GET.get('estado', 'pendientes')
#     query_busqueda = request.GET.get('q', '').strip()

#     # Todo tu universo base de seminarios (Tutor + Miembro)
#     como_tutor = Seminario.objects.filter(
#         comite__tutor=docente
#     ).select_related('alumno', 'comite', 'formulario_comite')

#     como_miembro = Seminario.objects.filter(
#         comite__miembro1=docente
#     ).select_related('alumno', 'comite', 'formulario_comite') | Seminario.objects.filter(
#         comite__miembro2=docente
#     ).select_related('alumno', 'comite', 'formulario_comite')

#     seminarios = []

#     # 1. FLUJO A: Si el usuario escribe una matrícula, busca en TODO sin importar los filtros
#     if query_busqueda:
#         condicion_matricula = Q(alumno__matricula__icontains=query_busqueda)

#         tutores_filtrados = como_tutor.filter(condicion_matricula)
#         miembros_filtrados = como_miembro.distinct().filter(condicion_matricula)

#         tutores_list = [{'seminario': s, 'rol': 'tutor'} for s in tutores_filtrados]
#         miembros_list = [{'seminario': s, 'rol': 'miembro'} for s in miembros_filtrados]

#         ids_tutor = {i['seminario'].pk for i in tutores_list}
#         miembros_list = [i for i in miembros_list if i['seminario'].pk not in ids_tutor]

#         seminarios = sorted(
#             tutores_list + miembros_list,
#             key=lambda i: (i['seminario'].numero, i['seminario'].periodo)
#         )

#         # Forzamos los estados visuales del dropdown a 'todos' para que coincida con la pantalla
#         rol = 'todos'
#         estado = 'todos'

#     # 2. FLUJO B: Si no hay búsqueda, funciona el comportamiento por defecto (Pendientes de cualquier rol)
#     else:
#         if rol == 'tutor':
#             seminarios_raw = [{'seminario': s, 'rol': 'tutor'} for s in como_tutor]
#         elif rol == 'miembro':
#             seminarios_raw = [{'seminario': s, 'rol': 'miembro'} for s in como_miembro.distinct()]
#         else:
#             tutores  = [{'seminario': s, 'rol': 'tutor'}   for s in como_tutor]
#             miembros = [{'seminario': s, 'rol': 'miembro'} for s in como_miembro.distinct()]
#             ids_tutor = {i['seminario'].pk for i in tutores}
#             miembros  = [i for i in miembros if i['seminario'].pk not in ids_tutor]
#             seminarios_raw = tutores + miembros

#         for item in sorted(seminarios_raw, key=lambda i: (i['seminario'].numero, i['seminario'].periodo)):
#             sem = item['seminario']
#             estado_form = 'pendiente'
#             if hasattr(sem, 'formulario_comite') and sem.formulario_comite:
#                 estado_form = sem.formulario_comite.estado_general

#             if estado == 'completados' and estado_form == 'completo':
#                 seminarios.append(item)
#             elif estado == 'pendientes' and estado_form == 'pendiente':
#                 seminarios.append(item)
#             elif estado == 'todos':
#                 seminarios.append(item)

#     # --- PANEL DE RECORDATORIOS (Independiente) ---
#     hoy = date.today()
#     todos_mis_seminarios = (Seminario.objects.filter(comite__tutor=docente) |
#                             Seminario.objects.filter(comite__miembro1=docente) |
#                             Seminario.objects.filter(comite__miembro2=docente)).distinct()

#     proximos_raw = todos_mis_seminarios.filter(fecha__gte=hoy).order_by('fecha', 'hora')
#     proximos_seminarios = []
#     for s in proximos_raw:
#         est_form = 'pendiente'
#         if hasattr(s, 'formulario_comite') and s.formulario_comite:
#             est_form = s.formulario_comite.estado_general
#         if est_form == 'pendiente':
#             r_label = 'Tutor' if s.comite.tutor == docente else 'Miembro'
#             proximos_seminarios.append({'seminario': s, 'rol': r_label})

#     return render(request, 'docente_seminario.html', {
#         'docente': docente,
#         'seminarios': seminarios,
#         'proximos_seminarios': proximos_seminarios,
#         'rol_activo': rol,
#         'estado_activo': estado,
#         'query_busqueda': query_busqueda,
#     })

# # ── Helpers ───────────────────────────────────────────────────

# def _rol_en_seminario(docente, seminario):
#     """Devuelve 'tutor', 'miembro1', 'miembro2' o None."""
#     c = seminario.comite
#     if c.tutor    == docente: return 'tutor'
#     if c.miembro1 == docente: return 'miembro1'
#     if c.miembro2 == docente: return 'miembro2'
#     return None


# def _get_o_crear_formulario(seminario):
#     f, _ = FormularioComite.objects.get_or_create(seminario=seminario)
#     return f


# # ── Vista principal de detalle ────────────────────────────────

# @login_required
# @user_passes_test(es_docente)
# def docente_seminario_detalle(request, seminario_id):
#     docente = request.user.docente
#     seminario = get_object_or_404(
#         Seminario.objects.select_related(
#             'alumno', 'comite',
#             'comite__tutor', 'comite__miembro1', 'comite__miembro2'
#         ).prefetch_related('evidencias'), # 👈 AQUÍ: Precarga todas las evidencias asociadas
#         pk=seminario_id
#     )

#     rol = _rol_en_seminario(docente, seminario)
#     # if not rol:
#     #     raise Http404

#     formulario  = _get_o_crear_formulario(seminario)
#     rol_activo  = request.GET.get('rol', 'todos')

#     # ── POST: tutor guarda el contenido del informe ───────────
#     if request.method == 'POST' and rol == 'tutor':
#         form = FormularioComiteForm(request.POST, instance=formulario)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Informe guardado correctamente.')
#             return redirect(
#                 'lumat_app:docente_seminario_detalle', seminario_id=seminario_id)
#     else:
#         form = FormularioComiteForm(instance=formulario) if rol == 'tutor' else None

#     # ── Formulario de firma / calificación ────────────────────
#     ya_firme = getattr(formulario, f'firma_{rol}')
#     firma_form = FirmaCalificacionForm() if not ya_firme else None

#     return render(request, 'docente_seminario_detalle.html', {
#         'docente':      docente,
#         'seminario':    seminario,
#         'formulario':   formulario,
#         'form':         form,
#         'firma_form':   firma_form,
#         'rol':          rol,
#         'rol_activo':   rol_activo,
#         'ya_firme':     ya_firme,
#     })

# # ── Vista: firmar + calificar ─────────────────────────────────

# @login_required
# @user_passes_test(es_docente)
# def docente_firmar_seminario(request, seminario_id):
#     if request.method != 'POST':
#         return redirect('lumat_app:docente_seminario_detalle',
#                         seminario_id=seminario_id)

#     docente   = request.user.docente
#     seminario = get_object_or_404(
#         Seminario.objects.select_related(
#             'comite', 'comite__tutor',
#             'comite__miembro1', 'comite__miembro2'),
#         pk=seminario_id)

#     rol = _rol_en_seminario(docente, seminario)
#     # if not rol:
#     #     raise Http404

#     formulario = _get_o_crear_formulario(seminario)

#     if getattr(formulario, f'firma_{rol}'):
#         messages.warning(request, 'Ya habías firmado este seminario.')
#         return redirect('lumat_app:docente_seminario_detalle',
#                         seminario_id=seminario_id)

#     form = FirmaCalificacionForm(request.POST)
#     if form.is_valid():
#         calif = form.cleaned_data['calificacion']

#         # Asignar calificación según rol
#         campo_calif = {
#             'tutor':    'calificacion_tutor',
#             'miembro1': 'calificacion_miembro1',
#             'miembro2': 'calificacion_miembro2',
#         }[rol]
#         setattr(formulario, campo_calif, calif)
#         setattr(formulario, f'firma_{rol}', True)
#         formulario.save()   # recalcula calificacion_final y estado_general

#         messages.success(request, 'Firma y calificación registradas.')
#     else:
#         messages.error(request, 'Datos inválidos. Verifica la calificación.')

#     return redirect('lumat_app:docente_seminario_detalle',
#                     seminario_id=seminario_id)


# # ── Vista: descargar PDF ──────────────────────────────────────

# @login_required
# @user_passes_test(es_docente)
# def docente_descargar_acta(request, seminario_id):
#     docente   = request.user.docente
#     seminario = get_object_or_404(
#         Seminario.objects.select_related(
#             'alumno', 'comite',
#             'comite__tutor', 'comite__miembro1', 'comite__miembro2'),
#         pk=seminario_id)

#     if not _rol_en_seminario(docente, seminario):
#         raise Http404

#     formulario = get_object_or_404(FormularioComite, seminario=seminario)

#     pdf_bytes = generar_pdf_comite(formulario)
#     nombre    = (f'acta_seminario_{seminario.numero}_'
#                  f'periodo_{seminario.periodo}_'
#                  f'{seminario.alumno.apellido_paterno}.pdf')

#     response = HttpResponse(pdf_bytes, content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="{nombre}"'
#     return response

# @login_required
# @user_passes_test(es_docente)
# def descargar_evidencias_zip(request, seminario_id):
#     seminario = get_object_or_404(Seminario, pk=seminario_id)
#     evidencias = seminario.evidencias.all()

#     if not evidencias:
#         messages.error(request, "Este seminario no tiene evidencias para descargar.")
#         return redirect('lumat_app:docente_seminario_detalle', seminario_id=seminario_id)

#     # Crear el archivo ZIP en memoria
#     buffer = io.BytesIO()
#     with zipfile.ZipFile(buffer, 'w') as zip_file:
#         for evidencia in evidencias:
#             if evidencia.archivo and os.path.exists(evidencia.archivo.path):
#                 # Usar el nombre guardado en la BD o el nombre del archivo físico
#                 nombre_archivo = evidencia.nombre or os.path.basename(evidencia.archivo.name)
#                 # Si el nombre no tiene extensión, se la agregamos de manera segura
#                 if not os.path.splitext(nombre_archivo)[1]:
#                     ext = os.path.splitext(evidencia.archivo.name)[1]
#                     nombre_archivo += ext

#                 zip_file.write(evidencia.archivo.path, nombre_archivo)

#     # Estructurar el nombre solicitado: nombre-semestre-periodo.zip
#     nombre_alumno = slugify(f"{seminario.alumno.nombre} {seminario.alumno.apellido_paterno}")
#     nombre_zip = f"{nombre_alumno}-semestre{seminario.alumno.semestre}-{slugify(seminario.periodo)}.zip"

#     response = HttpResponse(buffer.getvalue(), content_type='application/zip')
#     response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
#     return response

# def seminario(request):
#     return render(request, 'alumno_seminario.html', {
#         'fecha_seminario': '15 de mayo de 2026'
#     })

# ==========================================
# 3. GESTIÓN DEL PERFIL (MODO ROBUSTO)
# ==========================================


@login_required
def perfil_alumno(request):
    """
    Vista principal del perfil del alumno.
    Maneja la visualización y las acciones de edición.
    """
    try:
        # Intenta obtener la relación OneToOne.
        # Si el usuario es admin o docente, esto fallará de forma segura.
        alumno = request.user.alumno
    except (Alumno.DoesNotExist, AttributeError):
        messages.error(
            request,
            "Este usuario no cuenta con un perfil de alumno asociado.")
        return redirect('lumat_app:login')

    editando = request.GET.get('modo')  # 'perfil' | 'password' | None

    if request.method == 'GET':
        return _render_perfil(
            request, alumno,
            editando=editando,
            alumno_form=AlumnoEditForm(instance=alumno),
            password_form=PasswordChangeCustomForm(user=request.user),
        )

    # Manejo de acciones POST
    accion = request.POST.get('accion')

    if accion == 'perfil':
        return _guardar_perfil(request, alumno)

    if accion == 'password':
        return _cambiar_password(request, alumno)

    return redirect('lumat_app:perfil_alumno')

# Funciones auxiliares para mantener limpia la vista principal


def _render_perfil(request, alumno, editando, alumno_form, password_form):
    return render(request, 'alumno_perfil.html', {
        'alumno': alumno,
        'alumno_form': alumno_form,
        'password_form': password_form,
        'editando': editando,
    })


def _guardar_perfil(request, alumno):
    alumno_form = AlumnoEditForm(request.POST, instance=alumno)
    password_form = PasswordChangeCustomForm(user=request.user)

    if alumno_form.is_valid():
        alumno_form.save()
        messages.success(request, 'Perfil actualizado exitosamente')
        return redirect('lumat_app:perfil_alumno')

    messages.error(
        request, 'Datos inválidos, por favor verifica la información')
    return _render_perfil(
        request, alumno, editando='perfil',
        alumno_form=alumno_form,
        password_form=password_form,
    )


def _cambiar_password(request, alumno):
    alumno_form = AlumnoEditForm(instance=alumno)
    password_form = PasswordChangeCustomForm(
        user=request.user, data=request.POST)

    if password_form.is_valid():
        password_form.save()
        # Mantiene la sesión iniciada tras cambiar la contraseña
        update_session_auth_hash(request, password_form.user)
        messages.success(request, 'Contraseña actualizada exitosamente')
        return redirect('lumat_app:perfil_alumno')

    return _render_perfil(
        request, alumno, editando='password',
        alumno_form=alumno_form,
        password_form=password_form,
    )

# ADMINISTRACION


def admin_calendario_formulario_view(request):
    """Renderiza el nuevo formulario simplificado de fechas."""
    from django.contrib import admin

    calendarios_guardados = CalendarioGenerado.objects.all()

    context = {
        **admin.site.each_context(request),
        "title": "Generador Automático de Calendario de Seminarios",
        "calendarios": calendarios_guardados,
    }
    return render(request, "admin/calendario_form.html", context)


def _calcular_dias_habiles(fecha_inicio, fecha_fin):
    """Calcula el número de días laborables (Lunes a Viernes) en el rango."""
    dias_habiles = 0
    fecha_aux = fecha_inicio
    while fecha_aux <= fecha_fin:
        if fecha_aux.weekday() < 5:  # 0=Lunes, 1=Martes... 4=Viernes
            dias_habiles += 1
        fecha_aux += timedelta(days=1)
    return dias_habiles


def _validar_rango_calendario(fecha_inicio, fecha_fin, total_seminarios):
    """Valida las reglas de negocio temporales y la capacidad del rango."""
    hoy = datetime.now().date()

    if fecha_inicio < hoy:
        return "No se pueden generar calendarios en fechas anteriores a hoy."

    if fecha_inicio == fecha_fin:
        return "No se pueden generar calendarios de hoy a hoy mismo (mismo día)."

    if fecha_fin < fecha_inicio:
        return "La fecha inicial no puede ser posterior a la fecha final."

    dias_habiles = _calcular_dias_habiles(fecha_inicio, fecha_fin)
    total_slots = dias_habiles * 8  # 8 espacios diarios por hora (8am a 3pm)

    if total_seminarios > total_slots:
        return (
            f"El rango seleccionado solo contiene {total_slots} espacios "
            f"disponibles ({dias_habiles} días hábiles), pero necesitas "
            f"acomodar {total_seminarios} seminarios. Amplía el rango."
        )
    return None


def admin_calendario_generar_pdf_view(request):
    """
    Asigna fechas y horas consecutivas (8am a 3pm) omitiendo fines de semana,
    mezclando aleatoriamente a las personas y guardándolas en la base de datos.
    """
    if request.method != "POST":
        return redirect('calendar_form')

    fecha_inicio_str = request.POST.get("fecha_inicial")
    fecha_fin_str = request.POST.get("fecha_final")

    if not fecha_inicio_str or not fecha_fin_str:
        messages.error(request, "Ambas fechas son obligatorias.")
        return redirect('calendar_form')

    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

    seminarios_db = list(Seminario.objects.all())
    if not seminarios_db:
        messages.error(
            request, "No hay seminarios registrados en la base de datos.")
        return redirect('calendar_form')

    error_msg = _validar_rango_calendario(
        fecha_inicio, fecha_fin, len(seminarios_db))
    if error_msg:
        messages.error(request, error_msg)
        return redirect('calendar_form')

    random.shuffle(seminarios_db)

    agenda_sorteada = []
    fecha_actual = fecha_inicio
    horas_disponibles = list(range(8, 16))
    hora_idx = 0

    for seminario in seminarios_db:
        while fecha_actual.weekday() >= 5:
            fecha_actual += timedelta(days=1)
            hora_idx = 0

        # Calcular hora asignada
        actual_time = time(horas_disponibles[hora_idx], 0)

        # 🌟 PERSISTENCIA EN BD: Actualiza y guarda la asignación de cada registro
        seminario.fecha = fecha_actual
        seminario.hora = actual_time
        seminario.save()

        agenda_sorteada.append({
            "fecha": fecha_actual,
            "hora": actual_time,
            "nombre": str(seminario)
        })

        # Control de flujo horario secuencial
        hora_idx += 1
        if hora_idx >= len(horas_disponibles):
            hora_idx = 0
            fecha_actual += timedelta(days=1)

    # Compilar la estructura del contexto para la generación del PDF
    context_pdf = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "agenda": agenda_sorteada,
        "total_seminarios": len(agenda_sorteada)
    }

    html_string = render_to_string(
        "pdf/calendario_pdf_template.html", context_pdf)
    pdf_file = HTML(string=html_string).write_pdf()

    mes_inicio = fecha_inicio.strftime("%B")
    mes_fin = fecha_fin.strftime("%B %Y")
    nombre_periodo = f"Seminarios {mes_inicio} - {mes_fin}"

    nuevo_calendario = CalendarioGenerado(
        nombre=nombre_periodo, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
    )
    nombre_archivo = f"calendario_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"
    nuevo_calendario.archivo_pdf.save(nombre_archivo, ContentFile(pdf_file))
    nuevo_calendario.save()

    mensaje_exito = (
        f"¡Éxito! El {nombre_periodo} ha sido generado, "
        f"filtrado por días y horas hábiles y guardado localmente."
    )
    messages.success(request, mensaje_exito)
    return redirect('calendar_form')


def admin_estadisticas_view(request):
    """
    Calcula métricas del sistema y renderiza el
    Dashboard de estadísticas.
    """
    from django.contrib import admin

    total_alumnos = Alumno.objects.count()
    total_docentes = Docente.objects.count()
    total_seminarios = Seminario.objects.count()

    promedio_seminarios = round(
        total_seminarios / total_alumnos, 1) if total_alumnos > 0 else 0

    context = {
        **admin.site.each_context(request),
        "title": "Panel de Control e Indicadores LUMAT",
        "total_alumnos": total_alumnos,
        "total_docentes": total_docentes,
        "total_seminarios": total_seminarios,
        "promedio_seminarios": promedio_seminarios,
    }
    return render(request, "admin/estadisticas.html", context)


def admin_cambio_tutor_view(request):
    if request.method == "POST":
        sol_id = request.POST.get("solicitud_id")
        doc_id = request.POST.get("docente_id")
        accion = request.POST.get("accion")
        solicitud = SolicitudCambioTutor.objects.get(id=sol_id)

        if accion == "aprobar":
            if not doc_id:
                messages.error(
                    request,
                    "Debe seleccionar un nuevo tutor para aprobar la solicitud."
                )
                return redirect('/admin/cambio-tutor/')

            nuevo_tutor = Docente.objects.get(id=doc_id)
            comite = Comite.objects.filter(
                seminario__alumno=solicitud.alumno
            ).first()

            if comite:
                if nuevo_tutor in [comite.miembro1, comite.miembro2]:
                    messages.error(
                        request,
                        "El docente ya es miembro activo de este comité."
                    )
                    return redirect('/admin/cambio-tutor/')

                comite.tutor = nuevo_tutor
                comite.save()

            solicitud.estado = "aprobada"
            solicitud.resuelta_en = datetime.now()
            solicitud.save()
            messages.success(request, "Solicitud aprobada con éxito.")

        elif accion == "rechazar":
            solicitud.estado = "rechazada"
            solicitud.resuelta_en = datetime.now()
            solicitud.save()
            messages.error(request, "Solicitud rechazada.")
        return redirect('/admin/cambio-tutor/')

    from django.contrib import admin
    context = {
        **admin.site.each_context(request),
        "title": "Gestión de Cambio de Tutor",
        "solicitudes": SolicitudCambioTutor.objects.all(),
        "docentes": Docente.objects.all(),
    }
    return render(request, "admin/cambio_tutor.html", context)
