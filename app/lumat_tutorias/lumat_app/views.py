from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from weasyprint import HTML
from datetime import datetime, timedelta
import random
from django.core.files.base import ContentFile

from .models import Alumno, Docente, Seminario, CalendarioGenerado
from django.utils import timezone

from .models import (
    Evidencia,
    SolicitudCambioTutor
)
from .forms import (
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
            return reverse('lumat_app:docente_dashboard')
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


def es_docente(user):
    return user.groups.filter(name='Docente').exists()


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

@login_required
def seminario(request):
    """Redirige al seminario activo (el más reciente desbloqueado)."""
    alumno = request.user.alumno
    semestre = int(alumno.semestre)
    return redirect('lumat_app:seminario_detalle', num=semestre)


# ─────────────────────────────────────────────
# Vista: detalle de un seminario
# ─────────────────────────────────────────────

@login_required
def seminario_detalle(request, num):
    alumno = request.user.alumno
    semestre = int(alumno.semestre)

    # Validaciones de acceso
    if not (1 <= num <= 8):
        messages.error(request, "Número de seminario inválido.")
        return redirect(
            'lumat_app:seminario_detalle',
            num=semestre
        )

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
        nombre=archivo.name,
    )

    messages.success(request, "Evidencia subida correctamente.")
    return redirect('lumat_app:seminario_detalle',
                    num=seminario_obj.numero)


# ─────────────────────────────────────────────
# Vista: solicitar cambio de tutor
# ─────────────────────────────────────────────

@login_required
def cambio_tutor(request):
    alumno = request.user.alumno

    # Si ya tiene una solicitud pendiente, no permite crear otra
    if SolicitudCambioTutor.objects.filter(
        alumno=alumno, estado="pendiente"
    ).exists():
        messages.warning(
            request,
            "Ya tienes una solicitud de cambio de tutor en proceso.",
        )
        return redirect(
            "lumat_app:seminario_detalle", num=int(alumno.semestre)
        )

    if request.method == "POST":
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

    return render(request, "cambio_tutor.html", {"alumno": alumno})


@user_passes_test(es_docente)
def docente_dashboard(request):
    return render(request, 'docente_dashboard.html')


def seminario(request):
    return render(request, 'alumno_seminario.html', {
        'fecha_seminario': '15 de mayo de 2026'
    })

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
        return ("No se pueden generar calendarios de hoy a hoy mismo"
                " (mismo día).")

    if fecha_fin < fecha_inicio:
        return "La fecha inicial no puede ser posterior a la fecha final."

    dias_habiles = _calcular_dias_habiles(fecha_inicio, fecha_fin)
    if total_seminarios > dias_habiles:
        return (
            f"El rango seleccionado solo contiene {dias_habiles} días "
            f"hábiles, pero necesitas acomodar {total_seminarios} "
            f"seminarios. Amplía el rango de fechas."
        )
    return None


def admin_calendario_generar_pdf_view(request):
    """
    Asigna fechas consecutivas omitiendo fines de semana (Sábados y Domingos),
    mezclando aleatoriamente a las personas.
    """
    if request.method == "POST":
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
                request, "No hay seminarios registrados en la base de datos."
            )
            return redirect('calendar_form')

        error_msg = _validar_rango_calendario(
            fecha_inicio, fecha_fin, len(seminarios_db)
        )
        if error_msg:
            messages.error(request, error_msg)
            return redirect('calendar_form')

        random.shuffle(seminarios_db)

        agenda_sorteada = []
        fecha_actual = fecha_inicio

        for seminario in seminarios_db:
            while fecha_actual.weekday() >= 5:
                fecha_actual += timedelta(days=1)

            agenda_sorteada.append({
                "fecha": fecha_actual,
                "nombre": str(seminario)
            })
            fecha_actual += timedelta(days=1)

        # Compilar la plantilla del PDF
        context_pdf = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "agenda": agenda_sorteada,
            "total_seminarios": len(agenda_sorteada)
        }

        html_string = render_to_string(
            "pdf/calendario_pdf_template.html", context_pdf
        )
        pdf_file = HTML(string=html_string).write_pdf()

        # Guardar localmente en el servidor (MEDIA)
        mes_inicio = fecha_inicio.strftime("%B")
        mes_fin = fecha_fin.strftime("%B %Y")
        nombre_periodo = f"Seminarios {mes_inicio} - {mes_fin}"

        nuevo_calendario = CalendarioGenerado(
            nombre=nombre_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        nombre_archivo = (
            f"calendario_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"
        )
        nuevo_calendario.archivo_pdf.save(
            nombre_archivo, ContentFile(pdf_file))
        nuevo_calendario.save()

        mensaje_exito = (
            f"¡Éxito! El {nombre_periodo} ha sido generado, "
            f"filtrado por días hábiles y guardado localmente."
        )
        messages.success(request, mensaje_exito)
        return redirect('calendar_form')

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
