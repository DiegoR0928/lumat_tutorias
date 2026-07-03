from collections import defaultdict

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.urls import reverse
from lumat_app.acta_generador import generar_acta_alumno
from weasyprint import HTML
from datetime import datetime, timedelta, time
import random
from django.core.files.base import ContentFile
from django.db.models import Count, Q

from .models import ActaAlumnoData, Alumno, Docente, FormularioComite
from .models import Seminario, CalendarioGenerado, Comite
from django.utils import timezone

from .models import (
    Evidencia,
    SolicitudCambioTutor
)
from .forms import (
    ActaAlumnoForm,
    UserForm,
    AlumnoPerfilForm,
    AlumnoEditForm,
    AlumnoForm,
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

def _get_seminario_para_alumno(alumno, num):
    """
    Busca el seminario correspondiente para el alumno cargando el comité 
    con sus nuevos campos correspondientes (director, coodirector, asesor).
    """
    return Seminario.objects.filter(
        alumno=alumno, 
        numero=num
    ).select_related(
        'comite__tutor', 
        'comite__director',    
        'comite__coodirector', 
        'comite__asesor'        
    ).first()


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


@login_required
@user_passes_test(es_alumno)
def seminario_detalle(request, num):
    alumno = request.user.alumno
    semestre = int(alumno.semestre)

    # Validación: No permitir acceder a seminarios futuros
    if num > semestre:
        messages.warning(
            request,
            f"El seminario {num} estará disponible en semestres posteriores."
        )
        return redirect('lumat_app:seminario_detalle', num=semestre)

    # Obtiene el último intento (periodo) del seminario indicado
    seminario_obj = _get_seminario_para_alumno(alumno, num)
    comite = seminario_obj.comite if seminario_obj else None

    evidencias = (
        Evidencia.objects.filter(seminario=seminario_obj).order_by('subido_en')
        if seminario_obj else Evidencia.objects.none()
    )

    solicitud_pendiente = SolicitudCambioTutor.objects.filter(
        alumno=alumno,
        estado='pendiente'
    ).exists()

    # ========== Obtener estado de actas y formularios ==========
    formulario_comite = None
    acta_comite_url = None
    acta_existente = None

    if seminario_obj:
        if seminario_obj.actaComite:
            acta_comite_url = seminario_obj.actaComite.url

        try:
            formulario_comite = seminario_obj.formulario_comite
        except FormularioComite.DoesNotExist:
            pass

        # ¿Ya existe un acta de alumno guardada en la base de datos?
        acta_existente = ActaAlumnoData.objects.filter(
            seminario=seminario_obj).first()

    # Si ya existe, pre-rellenamos el formulario con los datos guardados (modo lectura)
    if acta_existente:
        form_acta = ActaAlumnoForm(initial=acta_existente.to_dict())
    else:
        # Intentamos recuperar datos que hayan fallado en la validación
        # del POST (enviados via sesión)
        session_form_data = request.session.pop('failed_acta_form_data', None)
        if session_form_data:
            form_acta = ActaAlumnoForm(session_form_data)
        else:
            form_acta = ActaAlumnoForm()

    comite_members = []
    if seminario_obj and seminario_obj.comite:
        c = seminario_obj.comite
        comite_members = [
            (c.tutor,       'Tutor'),
            (c.director,    'Director'),
            (c.coodirector, 'Coodirector'),
            (c.asesor,      'Asesor'),
        ]
    context = {
        'alumno': alumno,
        'num': num,
        'seminario': seminario_obj,
        'comite': comite,
        'evidencias': evidencias,
        'proximo_seminario': _proximo_seminario(alumno),
        'solicitud_pendiente': solicitud_pendiente,
        # 'periodo': seminario_obj.periodo if seminario_obj else None,
        'formulario_comite': formulario_comite,
        'acta_comite_url': acta_comite_url,
        'form_acta': form_acta,
        'acta_alumno_bloqueado': acta_existente is not None,
        'acta_alumno_existente': acta_existente,
        'comite_members': comite_members,
    }

    return render(request, 'alumno_seminario.html', context)


# =====================================================================
# 2. VISTA PROCESADORA: Recibe el POST del formulario del panel central
# =====================================================================
@login_required
@user_passes_test(es_alumno)
def generar_acta_view(request, num):
    alumno = request.user.alumno

    seminario = (
        Seminario.objects
        .filter(alumno=alumno, numero=num)
        # .order_by('-periodo')
        # .first()
    )

    if not seminario:
        messages.error(
            request, "No hay seminario registrado para este número.")
        return redirect("lumat_app:seminario_detalle", num=num)

    if not seminario.calificacion:
        messages.error(
            request, "Solo puedes generar el acta de un seminario completado.")
        return redirect("lumat_app:seminario_detalle", num=num)

    comite = seminario.comite
    acta_existente = ActaAlumnoData.objects.filter(seminario=seminario).first()

    if request.method == "POST":
        if acta_existente:
            messages.warning(
                request, "Tu acta ya fue generada y no puede modificarse.")
            return redirect("lumat_app:seminario_detalle", num=num)

        form = ActaAlumnoForm(request.POST)
        if form.is_valid():
            try:
                # 1. Guardar los datos en la base
                acta_existente = ActaAlumnoData.objects.create(
                    seminario=seminario,
                    **form.cleaned_data
                )

                # 2. Generar el PDF usando el buffer
                pdf_buffer = generar_acta_alumno(
                    seminario=seminario,
                    alumno=alumno,
                    comite=comite,
                    datos_form=acta_existente.to_dict(),
                )

                # 3. Guardar el archivo PDF directamente en el modelo Seminario
                nombre_archivo = f"acta_{num}_{alumno.matricula or alumno.id}.pdf"
                seminario.actaAlumno.save(
                    nombre_archivo,
                    ContentFile(pdf_buffer.read()),
                    save=True,
                )

                messages.success(
                    request, "Acta generada y guardada correctamente.")
                return redirect("lumat_app:seminario_detalle", num=num)

            except Exception as e:
                # Si falla la renderización, borramos la data huérfana para permitir reintentos
                ActaAlumnoData.objects.filter(seminario=seminario).delete()
                messages.error(
                    request, f"Error al generar el PDF técnico: {e}")
                return redirect("lumat_app:seminario_detalle", num=num)
        else:
            # Si el formulario tiene errores de validación, alertamos al usuario
            messages.error(
                request, "Por favor corrige los campos marcados en rojo antes de guardar.")
            # Guardamos temporalmente la data inválida en la sesión para no borrar lo
            # que el alumno escribió
            request.session['failed_acta_form_data'] = request.POST
            return redirect("lumat_app:seminario_detalle", num=num)

    # Si intentan ingresar por GET de manera manual, los regresamos al panel principal
    return redirect("lumat_app:seminario_detalle", num=num)


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

# ==========================================
# 3. GESTIÓN DEL PERFIL (MODO ROBUSTO)
# ==========================================


@login_required
@user_passes_test(es_alumno)
def perfil_alumno(request):
    alumno = get_object_or_404(Alumno, user=request.user)

    if request.method == 'POST':
        form = AlumnoPerfilForm(request.POST, request.FILES, instance=alumno)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('lumat_app:perfil_alumno')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = AlumnoPerfilForm(instance=alumno)

    return render(request, 'alumno_perfil.html', {
        'alumno': alumno,
        'form': form,
    })


def _render_perfil(request, alumno, editando, alumno_form, password_form):
    return render(request, 'alumno_perfil.html', {
        'alumno': alumno,
        'alumno_form': alumno_form,
        'password_form': password_form,
        'editando': editando,
    })


@login_required
def calendario(request):
    ultimo = CalendarioGenerado.objects.first()
    return render(request, 'alumno_calendario.html', {
        'calendario': ultimo,
    })


# ADMINISTRACION

def admin_calendario_formulario_view(request):
    """Renderiza el formulario administrativo para la gestión de fechas."""
    from django.contrib import admin

    calendarios_guardados = CalendarioGenerado.objects.all().order_by('-fecha_creacion')

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
    
    # Regla técnica: 6 bloques diarios de 1.5 horas de 8:00 AM a 5:00 PM
    total_slots = dias_habiles * 6  

    if total_seminarios > total_slots:
        return (
            f"El rango seleccionado solo contiene {total_slots} espacios "
            f"disponibles ({dias_habiles} días hábiles), pero necesitas "
            f"acomodar {total_seminarios} seminarios. Amplía el rango."
        )
    return None


def admin_calendario_generar_pdf_view(request):
    """
    Asigna fechas y horas consecutivas en bloques de 1.5 horas (8am a 5pm),
    priorizando semestres avanzados y manteniendo aleatoriedad interna.
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

    # Optimizamos la lectura de alumnos evitando el problema de consultas N+1
    seminarios_db = list(Seminario.objects.select_related('alumno').all())
    if not seminarios_db:
        messages.error(request, "No hay seminarios registrados en la base de datos.")
        return redirect('calendar_form')

    error_msg = _validar_rango_calendario(fecha_inicio, fecha_fin, len(seminarios_db))
    if error_msg:
        messages.error(request, error_msg)
        return redirect('calendar_form')

    # Agrupar a los alumnos por número de semestre
    sem_groups = defaultdict(list)
    for sem in seminarios_db:
        try:
            num_semestre = int(sem.alumno.semestre)
        except (ValueError, TypeError):
            num_semestre = 1
        sem_groups[num_semestre].append(sem)

    # Mezclar de forma aleatoria a los alumnos del mismo semestre
    for num_semestre in sem_groups:
        random.shuffle(sem_groups[num_semestre])

    # Unir la lista priorizando semestres más altos primero (Descendente)
    seminarios_ordenados = []
    for num_semestre in sorted(sem_groups.keys(), reverse=True):
        seminarios_ordenados.extend(sem_groups[num_semestre])

    agenda_sorteada = []
    fecha_actual = fecha_inicio
    
    # Configuración de los 6 bloques horarios de hora y media
    slots_horarios = [
        time(8, 0),    # 08:00 - 09:30
        time(9, 30),   # 09:30 - 11:00
        time(11, 0),   # 11:00 - 12:30
        time(12, 30),  # 12:30 - 14:00
        time(14, 0),   # 14:00 - 15:30
        time(15, 30),  # 15:30 - 17:00
    ]
    slot_idx = 0

    for seminario in seminarios_ordenados:
        # Omitir fines de semana saltando directo al siguiente lunes
        while fecha_actual.weekday() >= 5:
            fecha_actual += timedelta(days=1)
            slot_idx = 0

        actual_time = slots_horarios[slot_idx]

        # Guardar la planificación física en cada registro del modelo
        seminario.fecha = fecha_actual
        seminario.hora = actual_time
        seminario.save()

        agenda_sorteada.append({
            "fecha": fecha_actual,
            "hora": actual_time,
            "nombre": str(seminario)
        })

        # Avanzar al siguiente bloque de tiempo o al día de mañana
        slot_idx += 1
        if slot_idx >= len(slots_horarios):
            slot_idx = 0
            fecha_actual += timedelta(days=1)

    context_pdf = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "agenda": agenda_sorteada,
        "total_seminarios": len(agenda_sorteada)
    }

    html_string = render_to_string("pdf/calendario_pdf_template.html", context_pdf)
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

    messages.success(request, f"¡Éxito! El {nombre_periodo} ha sido generado correctamente.")
    return redirect('calendar_form')

def _parsear_periodo_a_fecha(periodo_str, es_fin=False):
    """
    Helper para aproximar texto de periodo (ej. '2022-1', '2023-2' o '2022') a un objeto date.
    Útil para calcular tiempos estimados si se guardan como strings.
    """
    try:
        if '-' in periodo_str:
            año, ciclo = periodo_str.split('-')
            año = int(año)
            # Ciclo 1 suele ser Enero, Ciclo 2 es Agosto
            mes = 1 if '1' in ciclo else 8
            return datetime(año, mes, 1).date()
        else:
            año = int(''.join(filter(str.isdigit, periodo_str)))
            mes = 12 if es_fin else 1
            return datetime(año, mes, 1).date()
    except Exception:
        return datetime.now().date()

def admin_estadisticas_view(request):
    """
    Calcula métricas analíticas complejas y genera las estructuras 
    para las tablas del Dashboard de indicadores LUMAT.
    """
    hoy = datetime.now().date()

    # ─────────────────────────────────────────────────────────
    # 1. TABLA: RELACIÓN ALUMNOS - PROFESORES (DIRECCIÓN ≤ 6)
    # ─────────────────────────────────────────────────────────
    docentes_query = Docente.objects.all()
    tabla_direcciones = []
    
    for docente in docentes_query:
        # Contamos cuántas veces funge como director o coodirector en comités activos
        num_director = Comite.objects.filter(director=docente).count()
        num_coodirector = Comite.objects.filter(coodirector=docente).count()
        total_tesis = num_director + num_coodirector
        
        tabla_direcciones.append({
            "docente": docente,
            "director": num_director,
            "coodirector": num_coodirector,
            "total": total_tesis,
            "excede_limite": total_tesis > 6,
            "alerta": total_tesis == 6
        })

    # ─────────────────────────────────────────────────────────
    # 2. TABLA: TIEMPO DE TITULACIÓN Y ATRASOS
    # ─────────────────────────────────────────────────────────
    alumnos_query = Alumno.objects.filter(estado__in=['activo', 'baja temporal']).order_by('apellido_paterno')
    tabla_titulacion = []
    
    for alumno in alumnos_query:
        fecha_inicio = _parsear_periodo_a_fecha(alumno.periodo_inicio_estudios, es_fin=False)
        
        # El doctorado dura 4 años (48 meses), la maestría 2 años (24 meses)
        años_limite = 4 if alumno.posgrado == 'doctorado' else 2
        
        try:
            # Intentamos calcular en base a la fecha de inicio estimada
            fecha_estimada_fin = fecha_inicio.replace(year=fecha_inicio.year + años_limite)
        except ValueError:
            # Manejo de años bisiestos
            fecha_estimada_fin = fecha_inicio + (datetime(fecha_inicio.year + años_limite, 3, 1).date() - datetime(fecha_inicio.year, 3, 1).date())

        # Calcular atraso si ya pasó la fecha estimada de fin
        atraso_meses = 0
        tiene_atraso = False
        
        if hoy > fecha_estimada_fin:
            tiene_atraso = True
            # Cálculo aproximado de meses de desfase
            desfase = hoy - fecha_estimada_fin
            atraso_meses = round(desfase.days / 30.4)

        tabla_titulacion.append({
            "alumno": alumno,
            "posgrado": alumno.get_posgrado_display(),
            "inicio": alumno.periodo_inicio_estudios,
            "fin_estimado": fecha_estimada_fin.strftime("%m/%Y"),
            "tiene_atraso": tiene_atraso,
            "atraso_meses": atraso_meses
        })

    # ─────────────────────────────────────────────────────────
    # 3. TABLA: ALUMNOS POR LÍNEA DE INVESTIGACIÓN
    # ─────────────────────────────────────────────────────────
    lineas_investigacion = Alumno.objects.values('linea_investigacion').annotate(total=Count('id')).order_by('-total')

    # ─────────────────────────────────────────────────────────
    # 4. TABLA: ACTAS FALTANTES POR SEMINARIO
    # ─────────────────────────────────────────────────────────
    seminarios_faltantes = Seminario.objects.select_related('alumno', 'comite').filter(
        Q(actaComite='') | Q(actaComite__isnull=True) | 
        Q(actaAlumno='') | Q(actaAlumno__isnull=True)
    ).order_by('alumno__apellido_paterno', 'numero')
    
    tabla_actas_faltantes = []
    for sem in seminarios_faltantes:
        falta_comite = not sem.actaComite
        falta_alumno = not sem.actaAlumno
        
        if falta_comite and falta_alumno:
            estatus_falta = "Ambas Actas"
        elif falta_comite:
            estatus_falta = "Acta del Comité"
        else:
            estatus_falta = "Acta del Alumno"
            
        tabla_actas_faltantes.append({
            "seminario": sem,
            "alumno": sem.alumno,
            "numero": sem.numero,
            "falta": estatus_falta
        })

# ─────────────────────────────────────────────────────────
    # 5. TABLA: ESTADOS DE ALUMNOS ACTUALES
    # ─────────────────────────────────────────────────────────
    estados_breakdown = Alumno.objects.values('estado').annotate(total=Count('id')).order_by('-total')
    
    dict_estados = {'activo': 'Activos', 'egresado': 'Egresados', 'dado de baja': 'Dados de Baja', 'baja temporal': 'Baja Temporal'}
    tabla_estados = [
        {"nombre": dict_estados.get(item['estado'], item['estado']), "total": item['total']}
        for item in estados_breakdown
    ]

    # 🌟 CORRECCIÓN AQUÍ: Importamos con alias para romper el conflicto de nombres
    from django.contrib import admin as django_admin

    context = {
        **django_admin.site.each_context(request),  # 🌟 Usamos el alias aquí
        "title": "Panel de Control e Indicadores LUMAT",
        "tabla_direcciones": tabla_direcciones,
        "tabla_titulacion": tabla_titulacion,
        "lineas_investigacion": lineas_investigacion,
        "tabla_actas_faltantes": tabla_actas_faltantes,
        "tabla_estados": tabla_estados,
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
                if nuevo_tutor in [comite.director, comite.coodirector]:
                    messages.error(
                        request,
                        "El docente ya es miembro activo de este comité."
                    )
                    return redirect('/admin/cambio-tutor/')

                comite.tutor = nuevo_tutor
                comite.save()

            solicitud.estado = "aprobada"
            solicitud.resuelta_en = timezone.now()
            solicitud.save()
            messages.success(request, "Solicitud aprobada con éxito.")

        elif accion == "rechazar":
            solicitud.estado = "rechazada"
            solicitud.resuelta_en = timezone.now()
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
