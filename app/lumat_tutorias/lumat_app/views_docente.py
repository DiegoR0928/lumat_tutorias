from email.headerregistry import Group

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.files.base import ContentFile

from .acta_generador import generar_acta_alumno

from .models import CalendarioGenerado, Docente, Seminario, FormularioComite
from .utils_pdf_comite import generar_pdf_comite
import io
import zipfile
from django.http import HttpResponse
from django.utils.text import slugify
from django.db.models import Q
from datetime import date
import os
from .forms import (
    DocenteForm,
    FirmaCalificacionForm,
    FormularioComiteForm,
    RegistroDocenteForm,
)
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse


def es_docente(user):
    return user.groups.filter(name='Docente').exists()


@login_required
def editar_perfil_docente(request):
    docente = get_object_or_404(Docente, user=request.user)

    if request.method == 'POST':
        form = DocenteForm(request.POST, request.FILES, instance=docente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('lumat_app:perfil_docente')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = DocenteForm(instance=docente)

    return render(request, 'docente_perfil.html', {
        'docente': docente,
        'form': form,
    })


ROLES_COMITE = ['tutor', 'director', 'coodirector', 'asesor']


def _obtener_universo_seminarios(docente):
    """Devuelve un dict {rol: queryset} para cada rol del comité."""
    base_qs = Seminario.objects.select_related(
        'alumno', 'comite', 'formulario_comite'
    )
    return {
        rol: base_qs.filter(**{f'comite__{rol}': docente})
        for rol in ROLES_COMITE
    }


def _combinar_todos(por_rol):
    """
    Recibe dict {rol: [items]} y devuelve lista unificada sin duplicados
    (gana el rol de menor índice), ordenada por número de seminario.
    """
    vistos = {}
    for rol in ROLES_COMITE:
        for item in por_rol.get(rol, []):
            pk = item['seminario'].pk
            if pk not in vistos:
                vistos[pk] = item
    return sorted(vistos.values(), key=lambda i: i['seminario'].numero)


def _filtrar_por_busqueda(universo, query):
    """Flujo A: filtra por matrícula en todos los roles."""
    condicion = Q(alumno__matricula__icontains=query)
    por_rol = {
        rol: [{'seminario': s, 'rol': rol} for s in qs.filter(condicion)]
        for rol, qs in universo.items()
    }
    return _combinar_todos(por_rol)


def _obtener_estado_formulario(seminario):
    """Determina de forma segura el estado general del formulario."""
    if hasattr(seminario, 'formulario_comite') and seminario.formulario_comite:
        return seminario.formulario_comite.estado_general
    return 'pendiente'


def _filtrar_por_rol_y_estado(universo, rol, estado):
    """Flujo B: filtra según los dropdowns de rol y estado."""
    roles_a_incluir = ROLES_COMITE if rol == 'todos' else [rol]

    por_rol = {
        r: [{'seminario': s, 'rol': r} for s in universo[r]]
        for r in roles_a_incluir
        if r in universo
    }
    candidatos = _combinar_todos(por_rol)

    if estado == 'todos':
        return candidatos

    return [
        item for item in candidatos
        if (
            (estado == 'completados' and _obtener_estado_formulario(item['seminario']) == 'completo') or
            (estado == 'pendientes' and _obtener_estado_formulario(item['seminario']) == 'pendiente')
        )
    ]


def _obtener_proximos_seminarios(docente):
    """Genera de forma limpia el panel de recordatorios independientes."""
    hoy = date.today()

    # Creamos la condición OR usando el conector nativo de Django,
    # sin operadores lógicos sueltos
    condicion_docente = (
        Q(comite__tutor=docente) |
        Q(comite__director=docente) |
        Q(comite__coodirector=docente) |
        Q(comite__asesor=docente)
    )
    proximos_raw = Seminario.objects.filter(
        condicion_docente,
        fecha__gte=hoy
    ).select_related('comite').order_by('fecha', 'hora').distinct()

    proximos = []
    for s in proximos_raw:
        if _obtener_estado_formulario(s) == 'pendiente':
            if s.comite.tutor == docente:
                rol_label = "Tutor"
            elif s.comite.director == docente:
                rol_label = "Director"
            elif s.comite.coodirector == docente:
                rol_label = "Coodirector"
            else:
                rol_label = "Asesor"
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

    universo = _obtener_universo_seminarios(docente)

    if query_busqueda:
        seminarios = _filtrar_por_busqueda(universo, query_busqueda)
        rol = 'todos'
        estado = 'todos'
    else:
        seminarios = _filtrar_por_rol_y_estado(universo, rol, estado)

    return render(request, 'docente_seminario.html', {
        'docente': docente,
        'seminarios': seminarios,
        'proximos_seminarios': _obtener_proximos_seminarios(docente),
        'ultimo_calendario': CalendarioGenerado.objects.first(),
        'rol_activo': rol,
        'estado_activo': estado,
        'query_busqueda': query_busqueda,
    })

# ── Helpers ───────────────────────────────────────────────────


def _rol_en_seminario(docente, seminario):
    """Devuelve 'tutor', 'director', 'coodirector' o 'asesor' o None."""
    c = seminario.comite
    if c.tutor == docente:
        return 'tutor'
    if c.director == docente:
        return 'director'
    if c.coodirector == docente:
        return 'coodirector'
    if c.asesor == docente:
        return 'asesor'

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
            'comite__tutor', 'comite__director',
            'comite__coodirector', 'comite__asesor'
        ).prefetch_related('evidencias'),
        pk=seminario_id
    )

    rol = _rol_en_seminario(docente, seminario)
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
        form = FormularioComiteForm(instance=formulario) if rol == 'tutor' else None

    # ── Firma acta comité ─────────────────────────────────────
    ya_firme = getattr(formulario, f'firma_{rol}') if rol else False
    firma_form = FirmaCalificacionForm() if not ya_firme else None

    # ── Acta del alumno ───────────────────────────────────────
    from .models import ActaAlumnoData
    acta_alumno = None
    ya_firme_alumno = False
    try:
        acta_alumno = seminario.acta_data
        if rol:
            ya_firme_alumno = getattr(acta_alumno, f'firma_{rol}', False)
    except ActaAlumnoData.DoesNotExist:
        pass
    firmas_comite = []
    firmas_alumno = []
    if seminario.comite:
        c = seminario.comite
        firmas_comite = [
            (c.tutor,       'Tutor',        formulario.firma_tutor,       formulario.calificacion_tutor),
            (c.director,    'Director',     formulario.firma_director,    formulario.calificacion_director),
            (c.coodirector, 'Coodirector',  formulario.firma_coodirector, formulario.calificacion_coodirector),
            (c.asesor,      'Asesor',       formulario.firma_asesor,      formulario.calificacion_asesor),
        ]
        if acta_alumno:
            firmas_alumno = [
                (c.director,    'Director',    getattr(acta_alumno, 'firma_director',    False)),
                (c.coodirector, 'Coodirector', getattr(acta_alumno, 'firma_coodirector', False)),
            ]
    acta_campos = []
    if acta_alumno:
        acta_campos = [
            ('Actividad principal', acta_alumno.actividad_principal),
            ('Cursos inscritos', acta_alumno.cursos),
            ('Artículos enviados / publicados', acta_alumno.articulos),
            ('Eventos académicos / estancias', acta_alumno.eventos),
            ('Plan de actividades siguiente semestre', acta_alumno.plan_siguiente),
            ('Comentarios adicionales', acta_alumno.comentarios),
        ]

    return render(request, 'docente_seminario_detalle.html', {
        'docente':          docente,
        'seminario':        seminario,
        'formulario':       formulario,
        'form':             form,
        'firma_form':       firma_form,
        'rol':              rol,
        'rol_activo':       rol_activo,
        'ya_firme':         ya_firme,
        'acta_alumno':      acta_alumno,
        'ya_firme_alumno':  ya_firme_alumno,
        'firmas_comite':    firmas_comite,
        'firmas_alumno':    firmas_alumno,
        'acta_campos':      acta_campos,
    })


@login_required
@user_passes_test(es_docente)
def docente_firmar_acta_alumno(request, seminario_id):
    if request.method != 'POST':
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    docente = request.user.docente
    seminario = get_object_or_404(
        Seminario.objects.select_related(
            'alumno', 'comite',
            'comite__tutor', 'comite__director',
            'comite__coodirector', 'comite__asesor'),
        pk=seminario_id)

    rol = _rol_en_seminario(docente, seminario)

    # Solo director y codirector pueden autorizar el acta del alumno
    if rol not in ('director', 'coodirector'):
        messages.error(
            request,
            'Solo el director y el codirector pueden autorizar el acta del alumno.'
        )
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    try:
        acta_alumno = seminario.acta_data
    except ActaAlumnoData.DoesNotExist:
        messages.error(request, 'El alumno aún no ha enviado su informe.')
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    campo_firma = f'firma_{rol}'
    if getattr(acta_alumno, campo_firma, False):
        messages.warning(request, 'Ya habías autorizado el acta del alumno.')
        return redirect('lumat_app:docente_seminario_detalle',
                        seminario_id=seminario_id)

    # Registrar la firma
    setattr(acta_alumno, campo_firma, True)
    acta_alumno.save()

    if acta_alumno.firmas_completas:
        try:
            pdf_buffer = generar_acta_alumno(
                seminario=seminario,
                alumno=seminario.alumno,
                comite=seminario.comite,
                datos_form=acta_alumno.to_dict(),
            )
            nombre_archivo = (
                f"acta_{seminario.numero}_"
                f"{seminario.alumno.matricula or seminario.alumno.id}.pdf"
            )
            seminario.actaAlumno.save(
                nombre_archivo,
                ContentFile(pdf_buffer.read()),
                save=True,
            )
            messages.success(
                request,
                "El director y el codirector autorizaron el acta. "
                "El PDF ha sido generado y está disponible para el alumno."
            )
        except Exception as e:
            messages.error(
                request,
                f"Las firmas se registraron pero ocurrió un error al generar el PDF: {e}"
            )
    else:
        pendientes = 2 - sum([
            acta_alumno.firma_director,
            acta_alumno.firma_coodirector,
        ])
        messages.success(
            request,
            f"Autorización registrada. "
            f"Falta {pendientes} firma para generar el acta."
        )

    return redirect('lumat_app:docente_seminario_detalle',
                    seminario_id=seminario_id)

def _verificar_y_generar_pdf_comite(request, seminario, formulario):
    if formulario.estado_general != 'completo':
        return  # todavía faltan firmas

    try:
        from .utils_pdf_comite import generar_pdf_comite
        from django.core.files.base import ContentFile

        seminario.calificacion = formulario.calificacion_final

        pdf_bytes = generar_pdf_comite(formulario)

        nombre_archivo = (
            f"acta_comite_{seminario.numero}_"
            f"{seminario.alumno.matricula or seminario.alumno.id}.pdf"
        )
        seminario.actaComite.save(
            nombre_archivo,
            ContentFile(pdf_bytes),
            save=True,  # también guarda seminario.calificacion
        )

        messages.info(
            request,
            "El sínodo se ha completado. Se ha generado y archivado el Acta del Comité."
        )

    except Exception as e:
        messages.error(
            request,
            f"Las firmas son válidas pero ocurrió un error al generar el PDF: {e}"
        )


def text_form_valido(form, request, formulario, rol):
    if form.is_valid():
        return True
    messages.error(request, "La calificación debe ser un número entre 0 y 10.")
    return False
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
            'comite__director', 'comite__coodirector', 'comite__asesor'),
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
            'director': 'calificacion_director',
            'coodirector': 'calificacion_coodirector',
            'asesor': 'calificacion_asesor',
        }[rol]
        setattr(formulario, campo_calif, calif)
        setattr(formulario, f'firma_{rol}', True)
        formulario.save()   # recalcula calificacion_final y estado_general
        _verificar_y_generar_pdf_comite(request, seminario, formulario)
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
            'comite__tutor', 'comite__director',
            'comite__coodirector', 'comite__asesor'),
        pk=seminario_id)

    if not _rol_en_seminario(docente, seminario):
        raise Http404

    formulario = get_object_or_404(FormularioComite, seminario=seminario)

    pdf_bytes = generar_pdf_comite(formulario)
    nombre = (f'acta_seminario_{seminario.numero}_'
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
    nombre_zip = f"{nombre_alumno}-semestre{alumno.semestre}-.zip"

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nombre_zip}"'
    return response

# R E G I S T R O D E  D O C E N T E S

def registro_docente(request):
    if request.method == 'POST':
        form = RegistroDocenteForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.cleaned_data

            user = User.objects.create_user(
                username=d['username'],
                email=d['email'],
                password=d['password1'],
            )
            user.is_active = False  # inactivo hasta que admin apruebe
            user.save()

            grupo, _ = Group.objects.get_or_create(name='Docente')
            user.groups.add(grupo)

            docente = Docente.objects.create(
                user=user,
                nombre=d['nombre'],
                apellido_paterno=d['apellido_paterno'],
                apellido_materno=d['apellido_materno'],
                correo=d['email'],
                telefono=d['telefono'],
                ultimo_grado_estudio=d['ultimo_grado_estudio'],
                universidad_o_centro=d['universidad_o_centro'],
                facultad_o_instituto=d['facultad_o_instituto'],
                red_social_investigacion=d['red_social_investigacion'],
                firma=request.FILES['firma'],
                nombramiento_sni=request.FILES.get('nombramiento_sni'),
            )

            # Correo al docente: "tu solicitud está en revisión"
            _correo_solicitud_recibida(user, docente)

            # Correo al admin: "nuevo docente esperando aprobación"
            _correo_admin_nuevo_docente(request, user, docente)

            messages.success(
                request,
                "Solicitud enviada. El administrador revisará tu registro y recibirás una notificación."
            )
            return redirect('lumat_app:registro_docente_pendiente')
    else:
        form = RegistroDocenteForm()

    return render(request, 'docente_registro.html', {'form': form})


def _correo_solicitud_recibida(user, docente):
    """Avisa al docente que su solicitud fue recibida y está en revisión."""
    send_mail(
        subject="Solicitud de registro recibida — LUMAT",
        message=(
            f"Hola {docente.nombre},\n\n"
            "Tu solicitud de registro como docente en LUMAT fue recibida correctamente. "
            "El administrador la revisará y recibirás un correo cuando tu cuenta sea activada.\n\n"
            "Sistema de Gestión Académica · UAZ"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def _correo_admin_nuevo_docente(request, user, docente):
    """Envía al admin un correo con los datos del docente y enlace para activar."""
    # Enlace para activar directo desde el correo
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    enlace_activar = request.build_absolute_uri(
        reverse('lumat_app:activar_docente', kwargs={
            'uidb64': uid,
            'token': token,
        })
    )
    # Enlace al admin de Django como alternativa
    enlace_admin = request.build_absolute_uri(
        f"/admin/auth/user/{user.pk}/change/"
    )

    cuerpo = render_to_string('emails/admin_nuevo_docente.html', {
        'docente': docente,
        'user': user,
        'enlace_activar': enlace_activar,
        'enlace_admin': enlace_admin,
    })

    send_mail(
        subject=f"Nuevo docente pendiente de aprobación: {docente.nombre} {docente.apellido_paterno}",
        message=(
            f"Nuevo registro de docente:\n"
            f"Nombre: {docente.nombre} {docente.apellido_paterno} {docente.apellido_materno}\n"
            f"Correo: {user.email}\n"
            f"Universidad: {docente.universidad_o_centro}\n\n"
            f"Activar cuenta: {enlace_activar}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        html_message=cuerpo,
        fail_silently=False,
    )


def activar_docente(request, uidb64, token):
    """El admin hace clic en el enlace del correo y activa la cuenta."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        # Avisar al docente que ya puede entrar
        _correo_cuenta_activada(user)

        messages.success(
            request,
            f"Cuenta de {user.username} activada correctamente. Se le notificó por correo."
        )
        return redirect('/admin/auth/user/')  # manda al admin de Django
    else:
        messages.error(request, "El enlace es inválido o ha expirado.")
        return redirect('/admin/')
    

def _correo_cuenta_activada(user):
    """Avisa al docente que el admin activó su cuenta."""
    send_mail(
        subject="Tu cuenta en LUMAT ha sido activada",
        message=(
            f"Hola {user.username},\n\n"
            "Tu cuenta de docente en LUMAT fue aprobada. Ya puedes iniciar sesión.\n\n"
            "Sistema de Gestión Académica · UAZ"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def registro_docente_pendiente(request):
    return render(request, 'docente_registro_pendiente.html')