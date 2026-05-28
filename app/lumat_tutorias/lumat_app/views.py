from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime, timedelta
import random
from django.core.files.base import ContentFile

from .models import Alumno, Docente, Seminario, CalendarioGenerado
from .forms import (
    UserForm,
    AlumnoForm,
    AlumnoEditForm,
    PasswordChangeCustomForm
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
            return '/docente/'
        elif user.groups.filter(name='Alumno').exists():
            return '/alumno/'

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


@login_required
def seminario_detalle(request, num):
    alumno = request.user.alumno
    semestre = int(alumno.semestre)  # asegúrate que sea convertible a int

    # Si el alumno intenta acceder a un seminario bloqueado
    if num > semestre or num < 1 or num > 8:
        # o una página de "acceso denegado"
        return redirect('lumat_app:seminario')

    return render(request, 'alumno_seminario.html', {
        'alumno': alumno,
        'num': num,
    })


@user_passes_test(es_docente)
def docente_dashboard(request):
    return render(request, 'docente_dashboard.html')


@user_passes_test(es_alumno)
def alumno_dashboard(request):
    return render(request, 'alumno_dashboard.html')


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

    # Traemos todos los calendarios que se han guardados en el servidor
    calendarios_guardados = CalendarioGenerado.objects.all()

    context = {
        **admin.site.each_context(request),
        "title": "Generador Automático de Calendario de Seminarios",
        "calendarios": calendarios_guardados,  # 🌟 Lo pasamos al template
    }
    return render(request, "admin/calendario_form.html", context)


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

        if (fecha_fin - fecha_inicio).days < 0:
            messages.error(
                request, "La fecha inicial no puede ser posterior a la fecha final.")
            return redirect('calendar_form')

        # 1. Obtener todos los seminarios de la base de datos
        seminarios_db = list(Seminario.objects.all())

        if not seminarios_db:
            messages.error(
                request, "No hay seminarios registrados en la base de datos.")
            return redirect('calendar_form')

        # 2. 📊 CONTAR DÍAS HÁBILES REALES EN EL RANGO SELECCIONADO
        dias_habiles_disponibles = 0
        fecha_aux = fecha_inicio
        while fecha_aux <= fecha_fin:
            if fecha_aux.weekday() < 5:  # 0=Lunes, 1=Martes... 4=Viernes
                dias_habiles_disponibles += 1
            fecha_aux += timedelta(days=1)

        # Validación inteligente basada solo en días laborables
        if len(seminarios_db) > dias_habiles_disponibles:
            messages.error(
                request,
                f"El rango seleccionado solo contiene {dias_habiles_disponibles} días hábiles, "
                f"pero necesitas acomodar {len(seminarios_db)} \
                seminarios. Amplía el rango de fechas."
            )
            return redirect('calendar_form')

        # 3. 🔀 Mezclar aleatoriamente a las personas
        random.shuffle(seminarios_db)

        # 4. 📅 ASIGNACIÓN CONSECUTIVA EN DÍAS HÁBILES
        agenda_sorteada = []
        fecha_actual = fecha_inicio

        for seminario in seminarios_db:  # Quité el sorted() que no era necesario
            # Si la fecha actual es Sábado (5) o Domingo (6), avanzamos hasta el Lunes
            while fecha_actual.weekday() >= 5:
                fecha_actual += timedelta(days=1)

            # Guardamos la asignación en el día laborable confirmado
            agenda_sorteada.append({
                "fecha": fecha_actual,
                "nombre": str(seminario)
            })

            # Preparamos el siguiente día calendario para el próximo ciclo
            fecha_actual += timedelta(days=1)

        # 5. Compilar la plantilla del PDF
        context_pdf = {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "agenda": agenda_sorteada,
            "total_seminarios": len(agenda_sorteada)
        }

        html_string = render_to_string(
            "pdf/calendario_pdf_template.html", context_pdf)
        pdf_file = HTML(string=html_string).write_pdf()

        # 6. Guardar localmente en el servidor (MEDIA)
        nombre_periodo = f"Seminarios {fecha_inicio.strftime('%B')} - {fecha_fin.strftime('%B %Y')}"
        nuevo_calendario = CalendarioGenerado(
            nombre=nombre_periodo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        nombre_archivo = f"calendario_{fecha_inicio_str}_al_{fecha_fin_str}.pdf"
        nuevo_calendario.archivo_pdf.save(
            nombre_archivo, ContentFile(pdf_file))
        nuevo_calendario.save()

        messages.success(
            request, f"¡Éxito! El {nombre_periodo} ha sido generado, \
            filtrado por días hábiles y guardado localmente.")
        return redirect('calendar_form')

    # Si no es POST, redirigir al formulario
    return redirect('calendar_form')


def admin_estadisticas_view(request):
    """Calcula métricas del sistema y renderiza el Dashboard de estadísticas."""
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
